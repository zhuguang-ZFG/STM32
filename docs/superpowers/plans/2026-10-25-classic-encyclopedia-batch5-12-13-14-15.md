# Batch 5 Chapters 12, 13, 14, and 15 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

I'm using the writing-plans skill to create the implementation plan.

**Goal:** 只加厚第 12、13、14、15 章（中文和英文一起），写成和第 00 到第 11 章相同的四块密度，每章一张可印刷的静态主图加一条短 GIF 辅图，把中容量 1 KB 页、500 kbit/s、48 MHz 与 67 字节、128 字和 `0x50` 改成和已冻结手册以及罗盘、附录 D 同一笔账，合入时把整书升到 1.3.0 · 2026-10-25，然后停下来等人复审。人接受之前不合入。

**Architecture:** 章号已经由设计锁死，不再打分重选，也不拆成四份计划。四章共用一次版本号、一次来源追加和一次人审。先只读这四章的中英八份，确认四块还不存在、旧坑标题还在。来源清单在 Task 2 按本计划里的 JSON 落盘，不在本计划提交里预先写入。然后生成静态 SVG 和短 GIF，再改八份正文。新出处只追加进 `stm32-book/manifest.json` 与 `stm32-book/manifest-en.json` 的 `sources`。附录 E 的卡片仍由 `stm32-book/build_html.py` 的 `source_registry_html()` 生成。主图走 `tools/svgkit.py` 的 `tools/gen_sample_figures.py`。短 GIF 走 `tools/gen_gifs.py` 的 `BUILDERS`。版本号同时写进两份 manifest、`stm32-book/revisions.json` 和 `stm32-book/README.md`。日期写死 `2026-10-25`，不取实施当天的日期。

**Tech Stack:** Python 3 标准库、现有 `stm32-book/build_html.py`、`python3 -m unittest`、`tools/svgkit.py`、`tools/gen_gifs.py`、`tools/minigfx.py`、`tools/check_assets.py`。不新增依赖，不改 `requirements.txt`。

单文件测试写成 `python3 stm32-book/tests/<file>.py -v`。`stm32-book/tests/` 不是 Python 包。整套测试仍用 `python3 -m unittest discover stm32-book/tests -v`。

本计划不拆成四个子计划。设计规格把这四章锁成同一批，版本只升一次到 1.3.0。拆开会把一次人审拆成四次，或者让 1.3.0 先带着不完整的四章合入。

本文件是实施计划。它不改章节正文，不画 SVG，不生成 GIF，不改 `stm32-book/` 的版本号。那些步骤留在后续实施 PR。

## Global Constraints

- 只把第 12、13、14、15 章加厚到和第 00 到第 11 章相同的四块密度。中文和英文一起写完。文件名仍是 `docs/12-Flash与IAP升级.md`、`docs/en/12-flash-iap.md`、`docs/13-CAN总线.md`、`docs/en/13-can.md`、`docs/14-USB.md`、`docs/en/14-usb.md`、`docs/15-FreeRTOS入门.md`、`docs/en/15-freertos.md`。
- 四块标题必须原样出现，各一次：中文 `## 原理与边界`、`## 关键插图`、`## 时序或状态`、`## 坑与出处卡`；英文 `## Principle and boundary`、`## Key figures`、`## Timing or state`、`## Pitfalls and source cards`。标题不加表情符号。四块插在 `<!-- /video: -->` 之后、该章现有的学习目标标题之前。
- 保留学习目标、硬件与接线、代码实现、动手实验、相关资源，以及英文文件里已经在用的对应标题。不要把英文标题改成另一章的措辞。在 `71c6723` 上，中文四章的学习目标都是 `## 📌 学习目标`，核心原理都是 `## 🧠 核心原理`。英文第 12、15 章是 `## 📌 Learning goals` 与 `## 🧠 Core ideas`。英文第 13、14 章是 `## 📌 Goals` 与 `## 🧠 Core idea`。这四套标题保持原样。
- 旧坑标题按文件里实际出现的那一行删掉，不留空标题。中文四章都是 `## ⚠️ 常见坑与排查`。英文第 12、15 章是 `## ⚠️ Pitfalls and troubleshooting`。英文第 13、14 章是 `## ⚠️ Pitfalls`，不是设计规格里那句较长的英文。不要先把第 13、14 章的标题改长再去扫描。设计规格把四章英文旧标题都写成了较长的那一串；以 `71c6723` 上的文件为准。
- 每章一张可印刷的静态主图：正常路径和失败路径都在图上。生成脚本是 `tools/gen_sample_figures.py`，画布是 `tools/svgkit.py`。不调用 `Svg.footer()`。落款用已有的 `_credit()`：左侧是文档号，右侧是「自绘 · 静态 · CC BY 4.0」。没有 `<animate`、`@keyframes`、`animation:`。图注写「自绘」，英文图注写 `Drawn for this book`。替代文本写结论。单张小于 60 KB。放不下就拆成主图加局部，每张仍争取小于 60 KB。第 12 章的第二张只允许叫 `assets/diagrams/sample-12-iap-vectors.svg`。第 13、14、15 章不另起第二张文件名。拆开仍超过时，在实施 PR 里写出字节数和原因，不把图画回简笔，也不把 60 KB 改成仓库新默认值。
- 另加一条短 GIF，只做网页和公众号辅图。GIF 不替换主图，也不是关键插图这一节唯一的图。四条都走 `tools/gen_gifs.py`，加入 `BUILDERS`。`minigfx.py` 只有 5×7 英文点阵，GIF 上的字用 ASCII。每条少于 500 KB。帧数不少于 3、不多于 12。`gen_gifs.chrome()` 自带的页脚可以留在 GIF 里。那条页脚不是静态主图的 `Svg.footer()`。
- 改写吸收的许可顺序：先用 ST 公开 RM/DS/PM 的事实、用自己的话重写；然后才是 MIT、BSD-2-Clause、BSD-3-Clause、ISC、CC BY 4.0、CC BY 3.0、CC0。GPL、LGPL、CC BY-NC、CC BY-ND、Apache-2.0、保留所有权利、未写许可的材料只留链接。不把厂商手册、USB-IF 原文、ISO 原文、官方插图或社区原文放进仓库。USB-IF 规范、ISO 11898、TJA1050 与 SN65HVD230 的厂商手册、pid.codes 的站点政策、FreeRTOS 网站正文，都不吸收句子。`usb20` 和 `freertos-priority` 保持「仅链接」。不吸收 libopencm3，不吸收 Apache-2.0 的 RT-Thread。
- 订货号是 STM32F103C8T6，LQFP48。读者看到的章号仍是文件名前缀加 1。源文件的一级标题继续带 `12`、`13`、`14`、`15`。这一批不改这个加 1。文件 `12` 在书里是第 13 章，`13` 是第 14 章，`14` 是第 15 章，`15` 是第 16 章。
- 第 12 章：中容量，闪存 64 KB，从 `0x08000000` 到 `0x08010000` 之前，1 KB 一页，共 64 页。页号 0 到 63。第 63 页从 `0x0800FC00` 起。`0x0801FC00` 越出 64 KB。Bootloader `0x08000000` 起 16 KB、16 页，到 `0x08004000` 之前。参数区 `0x08004000` 起 2 KB、2 页，到 `0x08004800` 之前。APP `0x08004800` 起 46 KB、46 页，长度 `0xB800`，到 `0x08010000` 之前。`16 + 2 + 46 = 64`。`0x08004800 + 0xB800 = 0x08010000`。解锁先写 KEY1 `0x45670123`，再写 KEY2 `0xCDEF89AB`。顺序反了，`CR.LOCK` 仍为 1。编程粒度是半字。擦除态 `0xFFFF`。按字节编程是 F4 的句子，在 C8 上作废。APP 第 0 字是 MSP，第 1 字在 `0x08004804`，是 `Reset_Handler`。`VTOR` 写成 `0x08004800`。`VTOR` 留在 0 是失败路径。无保护仍是 `0xA5`，只交叉引用第 01 章和 `pm0075-rdp`。`0xAA` 和 `0xCC` 在这颗料上作废。不把系统存储器 `0x1FFFF000` 画进用户闪存地图。页擦除「约 20~40 ms」留在核心原理，不进四块，也不进 snapshot。YMODEM 的 128 字节和 1024 字节留在核心原理，不进出处卡。
- 第 13 章：CAN1 内核时钟是 APB1 的 36 MHz。工作点：预分频 9，BS1 = 5，BS2 = 2，SJW = 1。时间份额 `Tq = 9 / 36e6 = 250` ns。一共 8 个时间份额。位时间 `8 × 250 ns = 2` µs，即 500 kbit/s。采样点 `(1 + 5) / 8 = 75%`，落在 1.5 µs。失败路径：预分频 8，BS1 = 6，BS2 = 3，10 个时间份额，`36e6 / (8 × 10) = 450` kbit/s，采样点 70%。1 Mbit/s 那一行（预分频 4，一共 9 个时间份额，采样点 66.7%）留在核心原理的表里，不进四块的工作点。工作脚是第 45 脚 PB8 = CAN_RX，第 46 脚 PB9 = CAN_TX。复位默认第 32 脚 PA11、第 33 脚 PA12 留给 USB，不画成这一章的正常路径。第 5 脚 PD0、第 6 脚 PD1 在 LQFP48 上存在，它们是 HSE。视频块里「C8 没有那两只脚」保持原字节。视频块以外不得再写这句。两端各 120 Ω 接在 CANH 与 CANL 之间。两只 120 Ω 并联的直流负载是 60 Ω。60 Ω 不是电缆特性阻抗。发送错误计数到 256 进入总线关闭。恢复是 128 次、每次 11 个连续隐性位。标准 ID 写入 `FilterIdHigh` 时左移 5。TJA1050 的 5 V 和 SN65HVD230 的 3.3 V 留在硬件节，不进出处卡，不进主图的规范主张。
- 第 14 章：`USBPRE = 0` 时 `72 / 1.5 = 48` MHz。`USBPRE = 1` 时 USB 时钟是 72 MHz。第 32 脚 PA11 = USB_DM，第 33 脚 PA12 = USB_DP。全速 1.5 kΩ 上拉接在 D+。这颗料的 USB 是全速设备，不是主机，也不是 480 Mbit/s。设备描述符长度 `0x12`，即 18 字节。`bMaxPacketSize0` 是 64。VID/PID 是 `0x1209/0x0001`，不是 `0x0483/0x5740`。配置集合 `wTotalLength` 是 `0x0043`，即 67。`bMaxPower` 的 `0x32` 是 100 mA。全速批量和中断上限 64 字节。1023 只属于全速等时。通知端点 8 字节是允许的。向量名默认 `USB_LP_CAN1_RX0`。USB-IF 的 10 ms 复位留在核心原理，不进出处卡。线宽和特性阻抗不进四块，除非手册印出欧姆数。没印出来就不编 90 Ω。片内上拉只有 RM0008 或 DS5319 印出了阻值才写进 snapshot。没印出阻值，图上仍标罗盘里的 1.5 kΩ，坑卡主张写成「罗盘已写 1.5 kΩ；手册这一版没有把阻值收进出处卡」。
- 第 15 章：`NVIC_PRIORITYGROUP_4`。`configTICK_RATE_HZ = 1000`，一个 tick 是 1 ms。HAL 时基是 TIM4，不是笼统的 TIMx。任务优先级数值大的先跑。KEY 是 2，LED 和 UART 是 1。`5 << (8 − 4) = 0x50`。调用 FromISR 的抢占优先级数值要大于等于 5。`EXTI0` 写成 5 是正常路径。写成 0 停在 `configASSERT`。数值 4 同样过急。LED 128 字 = 512 字节。KEY 192 字 = 768 字节。UART 256 字 = 1024 字节。先干 3 ms 再 `vTaskDelay(10)`，周期接近 13 ms。`vTaskDelayUntil` 的 10 ms 仍是 10 ms。互斥量有优先级继承，二值信号量没有。这颗 C8 没有 FPU。167 ns 和 17.2% 不进四块。实验节里的 64 字溢出留在实验，不进主图。
- 实施合入时把整书从 1.2.9 升到 **1.3.0**。中英文整书共用这个版本号。日期写死 **2026-10-25**。`accessed` 也写死 `2026-10-25`。不写成 1.2.10。不打 tag，不创建 GitHub Release。本计划提交不升版本。
- Book CI 变绿之后停下来等人复审。复审对象是构建出的中英 HTML 里的这四章。人接受之前不合入，也不开下一批章。CI 变绿不等于可以自动 squash 合入。
- 实施基线是 #54 合入之后的 `main` 尖端。写本计划时该尖端是 `71c67230cddd8d24fcfcd416b56acf3187962731`（`docs: 第 12、13、14、15 章加厚设计 (#54)`）。其章节正文与 v1.2.9 `adc5cd7ae2314195f5214a48ffdfc53e69f76851` 相同，只多了设计规格。
- 不加厚除 12、13、14、15 以外的任何章，含 00–11 和 16–28。不重选样本。不改 `docs/superpowers/plans/` 里已有的锁定文件和来源清单。不改 `tools/scan_sample_chapters.py`、`tools/scan_batch2_chapters.py`、`tools/scan_batch3_chapters.py`、`tools/scan_batch4_chapters.py`。不改总纲、Batch2、Batch3、Batch4 规格、观感规格、海报规格、密度规格、CONTENT_GUIDE 规格，也不改两份 `CONTENT_GUIDE.md`。不改本批设计规格 `docs/superpowers/specs/2026-10-25-classic-encyclopedia-batch5-12-13-14-15-design.md`。
- 不改 `stm32-book/build_html.py`。出版书签仍是现在的 44 条。不把新的二级标题收进书签。不改密度刀 F 的令牌、`stm32-book/styles/book.css`、`stm32-book/styles/tokens.json` 和间距。不把样式、字号、行长或页边再收一刀。
- 不改附录 A 的既有契约，不改附录 D 已有各行的算术，不手改 `stm32-book/book/E-参考资料.md` 或英文对应文件。不把 500 kbit/s 或 IAP 地图新写成附录 D 的一行。不删 `test_build.py` 里 `0x271`、`167 ns`、账本名和出版书签长度为 44 的断言。不放宽 `test_sample_chapters.py`、`test_batch2_chapters.py`、`test_batch3_chapters.py` 或 `test_batch4_chapters.py`。不新增读取 `CONTENT_GUIDE.md` 的测试。不改 CSS 哈希一类的视觉契约。
- 不删除、不重画已有图。第 12 章留下 `flash-iap.svg`。第 13 章留下 `can-arbitration.svg`。第 14 章留下 `usb-enumeration.svg`。第 15 章留下 `freertos-scheduler.svg`。不重画 `sample-00-boot-state.svg`、`sample-01-swd-vectors.svg`、`sample-02-clock-tree.svg`、`sample-03-gpio-led.svg`、`sample-04-exception-stack.svg`、`sample-05-pwm-1khz.svg`、`sample-06-uart-frame.svg`、`sample-07-i2c-addr.svg`、`sample-08-spi-jedec.svg`、`sample-09-adc-sar.svg`、`sample-10-dma-cndtr.svg`、`sample-11-iwdg-1s.svg`。不改已有 16 个 BUILDERS 的像素：`led-blink`、`pwm-breath`、`uart-bits`、`i2c-timing`、`dma-ring`、`sar-adc`、`nvic-preempt`、`uart-idle`、`clock-css`、`pwm-1khz`、`spi-jedec`、`adc-sample`、`swd-fetch`、`i2c-addr`、`dma-cndtr`、`iwdg-1s`。不把 `tools/svg2gif.py` 当成必经步骤。不改 `assets/video/`，不改 `tools/gen_narrated.py`。`<!-- video: -->` 与 `<!-- /video: -->` 之间的旁白保持原样，包括第 13 章旁白里那句「C8 没有那两只脚」。旁白不重录。不重画 29 张讲解海报。
- 新来源 id 只追加，顺序固定为 `rm0008-flash`、`rm0008-can`、`ds5319-usbcan`、`rm0008-usb`、`freertos-syscall`。没有第六个 id。片内上拉的阻值若印在手册里，写进已有的新 id snapshot，不为此再开一个 id。已有 id 的对象一个字段都不改，含 `rm0008`、`ds5319`、`rm0008-rcc`、`ds5319-clock`、`ds5319-i2c`、`ds5319-swd`、`pm0075-rdp`、`pm0056`、`pm0056-vector`、`pm0056-nvic`、`project-examples`、`rm0090`、`usb20`、`freertos-priority`、`freertos-1132`、`an2606`、`an3965`。中英两份 manifest 的 `url`、`snapshot`、`license`、`accessed` 用同一串字符；`title`、`authority`、`scope` 用对应语言。
- 代码继续按 `docs/CONTENT_GUIDE.md`：HAL，参数用宏。不新开可烧录工程。不改 `examples/iap-bootloader/`、`examples/can-bxcan/`、`examples/usb-cdc/`、`examples/usb-hid/`、`examples/freertos-task/`。例程里「小容量」和「48 脚封装没有」这两句留在例程。
- 不加图目录或表目录，不加第 30 章，不改 `docs/00`–`28` 的文件名。不预选文件 `16` 或 `28` 作为下一批。
- 脚号默认第 32 脚 PA11、第 33 脚 PA12，第 45 脚 PB8、第 46 脚 PB9。实施时打开与 `ds5319-clock` 同一份 DS5319 Rev 20 表 5。印出的脚号不同就改脚号，信号名按印出的复用列，并在实施 PR 里写明。USB 章号默认第 23 章，向量名默认 `USB_LP_CAN1_RX0`。CAN 章号默认第 21 章。过滤器默认与例程一致：标准 ID 放在 `FilterIdHigh`，左移 5。FreeRTOS 默认左移 `(8 − 4)`，EXTI 用 5，得到 `0x50`。印出的文字不同就改 snapshot，500 kbit/s、48 MHz、「设备不是主机」和例程里的 5 不变。不编 CAN 基址。不把 21 再左移进 `FilterIdHigh`。
- 同一对脚：第 13 章主图主张 PB8/PB9 上的 CAN。第 14 章主图主张 PA11/PA12 上的 USB。第 07 章已经主张 PB8/PB9 不是 I2C 的正常路径。三张图都不把两种功能画成同时有效。不重画第 02 章的时钟树，不重画第 04 章的入栈，不重画第 01 章的两字图。

## File map

| 路径 | 责任 |
| --- | --- |
| `tools/scan_batch5_chapters.py` | 只读 12、13、14、15 的中英八份，确认四块缺失、旧坑标题还在。英文旧标题按文件区分 |
| `docs/superpowers/plans/2026-10-25-batch5-12-13-14-15-lock.json` | Task 1 运行时写出。`baseline` 等于当时的 `git rev-parse HEAD`。本计划提交不包含这份文件 |
| `docs/superpowers/plans/2026-10-25-batch5-12-13-14-15-source-list.json` | Task 2 按下面的 JSON 落盘。五个 absorb id，社区列表为空。登记以 manifest 为准 |
| `tools/gen_sample_figures.py` | 在现有十二张静态主图之外追加四张。不改已有十二个函数，不改 `_credit` |
| `assets/diagrams/sample-12-iap-map.svg` | 第 12 章主图 |
| `assets/diagrams/sample-13-can-bit.svg` | 第 13 章主图 |
| `assets/diagrams/sample-14-usb-enum.svg` | 第 14 章主图 |
| `assets/diagrams/sample-15-rtos-prio.svg` | 第 15 章主图 |
| `assets/diagrams/sample-12-iap-vectors.svg` | 只有第 12 章主图达到或超过 60 KB 时才允许出现 |
| `tools/gen_gifs.py` | `BUILDERS` 末尾追加 `iap-jump`、`can-500k`、`usb-48m`、`rtos-tick`。不改已有十六个函数 |
| `assets/gif/iap-jump.gif` | 第 12 章辅图。只画钥匙顺序、半字和两字的正常路径 |
| `assets/gif/can-500k.gif` | 第 13 章辅图。只画 8 个时间份额和 500 kbit/s |
| `assets/gif/usb-48m.gif` | 第 14 章辅图。只画 D+ 上拉、48 MHz、18 字节和 67 字节 |
| `assets/gif/rtos-tick.gif` | 第 15 章辅图。只画 1 ms、优先级 2 和 128 字 |
| `assets/README.md` | 登记四张 SVG 和四条 GIF，并把四张旧动画标成辅图。第五节「上面 16 张」改为「上面 20 张」 |
| 八份章节 Markdown | 四块，以及和罗盘、附录 D、手册冲突的那几格。视频块字节不变 |
| `stm32-book/manifest.json` 与 `stm32-book/manifest-en.json` | 五个新 `sources`、四章罗盘、版本号 |
| `stm32-book/revisions.json` | 1.3.0 修订条目，插在数组最前 |
| `stm32-book/README.md` | 当前版本句，以及「也不要把 1.2.9 的产物标成 1.3.0」 |
| `CREDITS.md` | 第六节下面增加 v1.3.0 小节。静态框图张数改为 22。若拆出第二张第 12 章 SVG，改为 23。光栅动画个数改为 20 |
| `stm32-book/tests/test_batch5_sources.py` | 来源清单的许可门 |
| `stm32-book/tests/test_batch5_chapters.py` | 四块、共享数字、主图、GIF |
| `stm32-book/tests/test_build.py` | 只改当前版本断言。`0x271` 和书签条数保留 |

---

### Task 1: Gap scan and lock

**Files:**
- Create: `tools/scan_batch5_chapters.py`
- Create: `docs/superpowers/plans/2026-10-25-batch5-12-13-14-15-lock.json`（脚本在退出码 0 时写出。本计划提交里还没有它）

**Interfaces:**
- Consumes: 八份原稿。不读别的章，不调用 `tools/scan_sample_chapters.py`，不调用 `tools/scan_batch2_chapters.py`，不调用 `tools/scan_batch3_chapters.py`，不调用 `tools/scan_batch4_chapters.py`。
- Produces: 锁定文件字段 `rubric`（字符串 `"2026-10-25-classic-encyclopedia-batch5-12-13-14-15"`）、`baseline`（40 位十六进制，等于运行时 `git rev-parse HEAD`）、`chapters`（`["12", "13", "14", "15"]`）、`four_blocks_absent`（`true`）、`old_pitfall_heading_present`（`true`）、`files`。`files` 的键是 `"12"`、`"13"`、`"14"`、`"15"`。每个值有 `zh`、`en`、`zh_four_blocks`、`en_four_blocks`、`zh_old_pitfall`、`en_old_pitfall`、`en_old_heading`。后面的任务只改这四个前缀。

四块标题是中文 `## 原理与边界`、`## 关键插图`、`## 时序或状态`、`## 坑与出处卡`，英文 `## Principle and boundary`、`## Key figures`、`## Timing or state`、`## Pitfalls and source cards`。

旧坑标题按文件区分：

| 前缀 | 中文旧标题 | 英文旧标题 |
| --- | --- | --- |
| `12` | `## ⚠️ 常见坑与排查` | `## ⚠️ Pitfalls and troubleshooting` |
| `13` | `## ⚠️ 常见坑与排查` | `## ⚠️ Pitfalls` |
| `14` | `## ⚠️ 常见坑与排查` | `## ⚠️ Pitfalls` |
| `15` | `## ⚠️ 常见坑与排查` | `## ⚠️ Pitfalls and troubleshooting` |

在 `71c67230cddd8d24fcfcd416b56acf3187962731` 上，这八份都还没有四块，上表的旧坑标题都还在。若执行时任何一份已经有四块，或者旧标题已经不在，脚本退出码 2，不改写锁定文件，后面的任务停。不要在已有四块上再叠一套标题。不要把第 13、14 章的英文旧标题先改成长标题。

- [ ] **Step 1: 写入核对脚本**

把下面的程序保存为 `tools/scan_batch5_chapters.py`。

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Confirm chapters 12, 13, 14, and 15 are still missing the four blocks.

Run from the repository root:

    python3 tools/scan_batch5_chapters.py

Rewrites docs/superpowers/plans/2026-10-25-batch5-12-13-14-15-lock.json and
exits 0 when all eight manuscripts lack the four headings and still have the
old pitfall heading that is actually in that file. English chapters 13 and 14
use the shorter heading "## ⚠️ Pitfalls". Exits 2 without writing the lock if
a four-block heading is already present, or if the old pitfall heading is
already gone. Does not score other chapters and does not touch earlier locks.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch5-12-13-14-15-lock.json"
FILES = {
    "12": (
        ROOT / "docs" / "12-Flash与IAP升级.md",
        ROOT / "docs" / "en" / "12-flash-iap.md",
        "## ⚠️ Pitfalls and troubleshooting",
    ),
    "13": (
        ROOT / "docs" / "13-CAN总线.md",
        ROOT / "docs" / "en" / "13-can.md",
        "## ⚠️ Pitfalls",
    ),
    "14": (
        ROOT / "docs" / "14-USB.md",
        ROOT / "docs" / "en" / "14-usb.md",
        "## ⚠️ Pitfalls",
    ),
    "15": (
        ROOT / "docs" / "15-FreeRTOS入门.md",
        ROOT / "docs" / "en" / "15-freertos.md",
        "## ⚠️ Pitfalls and troubleshooting",
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
    for prefix, (zh_path, en_path, en_old) in FILES.items():
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
            "zh_old_pitfall": ZH_OLD in zh,
            "en_old_pitfall": en_old in en,
            "en_old_heading": en_old,
        }
        payload_files[prefix] = row
        if row["zh_four_blocks"] or row["en_four_blocks"]:
            print(f"{prefix} already has a four-block heading; stop", file=sys.stderr)
            blocked = True
        if not row["zh_old_pitfall"] or not row["en_old_pitfall"]:
            print(f"{prefix} is missing the old pitfall heading; stop", file=sys.stderr)
            blocked = True
        print(
            f"{prefix} four_blocks={'yes' if row['zh_four_blocks'] or row['en_four_blocks'] else 'no'} "
            f"old_pitfall={'yes' if row['zh_old_pitfall'] and row['en_old_pitfall'] else 'no'}"
        )
    if blocked:
        return 2
    baseline = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    payload = {
        "rubric": "2026-10-25-classic-encyclopedia-batch5-12-13-14-15",
        "baseline": baseline,
        "chapters": ["12", "13", "14", "15"],
        "four_blocks_absent": True,
        "old_pitfall_heading_present": True,
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

Run: `python3 tools/scan_batch5_chapters.py`

Expected: 退出码 0，标准输出含

```text
12 four_blocks=no old_pitfall=yes
13 four_blocks=no old_pitfall=yes
14 four_blocks=no old_pitfall=yes
15 four_blocks=no old_pitfall=yes
baseline=
```

`baseline=` 后面是当时 `git rev-parse HEAD` 的 40 位哈希。锁定文件里 `chapters` 仍为 `["12", "13", "14", "15"]`，`four_blocks_absent` 仍为 `true`，`old_pitfall_heading_present` 仍为 `true`。`files["13"]["en_old_heading"]` 是 `## ⚠️ Pitfalls`。`files["14"]["en_old_heading"]` 同样是 `## ⚠️ Pitfalls`。`files["12"]["en_old_heading"]` 和 `files["15"]["en_old_heading"]` 是 `## ⚠️ Pitfalls and troubleshooting`。这个 HEAD 必须还没有新的 `sources`，也还没有四块。

若退出码为 2：停止。不要改四块标题去凑退出码 0，也不要把第 13、14 章的英文旧标题改长。

- [ ] **Step 3: 确认更早的锁定、扫描脚本和设计规格没被改写**

Run:

```bash
git diff --name-only -- docs/superpowers/plans/2026-10-25-sample-chapter-lock.json docs/superpowers/plans/2026-10-25-sample-source-list.json docs/superpowers/plans/2026-10-25-batch2-04-06-lock.json docs/superpowers/plans/2026-10-25-batch2-04-06-source-list.json docs/superpowers/plans/2026-10-25-batch3-02-05-08-09-lock.json docs/superpowers/plans/2026-10-25-batch3-02-05-08-09-source-list.json docs/superpowers/plans/2026-10-25-batch4-01-07-10-11-lock.json docs/superpowers/plans/2026-10-25-batch4-01-07-10-11-source-list.json docs/superpowers/specs/2026-10-25-classic-encyclopedia-thicken-design.md docs/superpowers/specs/2026-10-25-classic-encyclopedia-batch2-04-06-design.md docs/superpowers/specs/2026-10-25-classic-encyclopedia-batch3-02-05-08-09-design.md docs/superpowers/specs/2026-10-25-classic-encyclopedia-batch4-01-07-10-11-design.md docs/superpowers/specs/2026-10-25-classic-encyclopedia-batch5-12-13-14-15-design.md tools/scan_sample_chapters.py tools/scan_batch2_chapters.py tools/scan_batch3_chapters.py tools/scan_batch4_chapters.py
```

Expected: 无输出。

- [ ] **Step 4: Commit**

```bash
git add tools/scan_batch5_chapters.py docs/superpowers/plans/2026-10-25-batch5-12-13-14-15-lock.json
git commit -m "docs: 锁定第 12、13、14、15 章尚未加厚"
```

这一笔提交里不要带 manifest 或章节正文。锁定文件里的 `baseline` 必须仍指向还没有新 `sources` 的那次提交。

### Task 2: Source list with the license gate

**Files:**
- Create: `docs/superpowers/plans/2026-10-25-batch5-12-13-14-15-source-list.json`
- Create: `stm32-book/tests/test_batch5_sources.py`
- Test: `stm32-book/tests/test_batch5_sources.py`

**Interfaces:**
- Consumes: Task 1 的 `chapters == ["12", "13", "14", "15"]`，以及 `four_blocks_absent == true`。
- Produces: 五个新 id，顺序固定为 `rm0008-flash`、`rm0008-can`、`ds5319-usbcan`、`rm0008-usb`、`freertos-syscall`。不产生第六个 id。`community` 是空数组。`reuse_existing` 的 id 顺序是 `pm0075-rdp`、`pm0056-vector`、`ds5319-swd`、`ds5319-clock`、`rm0008-rcc`、`ds5319-i2c`、`project-examples`、`rm0090`。这八个 id 不新建 manifest 对象。`usb20`、`freertos-priority`、`freertos-1132`、`an2606`、`an3965`、`pm0056`、`pm0056-nvic` 也不新建，也不改字段。

2026-10-25 设计规格冻结的事实，实施时打开同一批 URL。首页修订或节号变了就停，先改清单里的 `snapshot` 和 `section`，再画图、再写正文。数字本身不变：

- RM0008 Rev 21（February 2021）。闪存默认第 3 章。bxCAN 默认第 21 章。USB 设备默认第 23 章。PDF 与已有 `rm0008-rcc` 相同。
- DS5319 Rev 20（July 2025）表 5。PDF 与已有 `ds5319-clock` 相同。
- FreeRTOS Kernel V11.3.2，与已有 `freertos-1132` 同一份发行标签。许可字符串写 `MIT`。

打开这些 URL：

- `https://www.st.com/resource/en/reference_manual/rm0008-stm32f101xx-stm32f102xx-stm32f103xx-advanced-arm-based-32-bit-mcus-stmicroelectronics.pdf`
- `https://www.st.com/resource/en/datasheet/stm32f103c8.pdf`
- `https://github.com/FreeRTOS/FreeRTOS-Kernel/releases/tag/V11.3.2`

三份里有打不开的就停。不要换一份别的手册来补页大小、基址、上拉阻值或另一个向量名。

社区例程这一批不冻结。来源清单的 `community` 是空数组。例程主张走已有的 `project-examples`，不新开例程 id。不吸收未写许可的博客，不吸收 GPL 的 libopencm3，不吸收 Apache-2.0 的 RT-Thread，不吸收 USB-IF 和 ISO 的句子，不吸收收发器厂商手册。

- [ ] **Step 1: 写入来源清单**

把下面的 JSON 保存为 `docs/superpowers/plans/2026-10-25-batch5-12-13-14-15-source-list.json`。实施时不要另写一份。许可门测试去读这份文件。

```json
{
  "chapters": ["12", "13", "14", "15"],
  "community": [],
  "reuse_existing": [
    {
      "id": "pm0075-rdp",
      "claim": "On STM32F103C8T6 the unprotected RDP byte is 0xA5. Programming that key back first mass-erases main Flash. 0xAA and 0xCC are void on this part.",
      "do_not_copy": "Do not edit the existing pm0075-rdp object. Do not redraw the chapter 01 key figure. Do not expand watchdog feeding in chapter 12."
    },
    {
      "id": "pm0056-vector",
      "claim": "Word 0 is the initial MSP and word 1 is Reset. The application VTOR points at 0x08004800. The reset word is at 0x08004804.",
      "do_not_copy": "Do not edit the existing pm0056-vector object. Do not paste the vector table. Do not put 167 ns in chapter 12."
    },
    {
      "id": "ds5319-swd",
      "claim": "STM32F103x8 Flash is 64 KB. The last page of this C8 starts at 0x0800FC00. 0x0801FC00 is the last page of a 128 KB part and is out of range here.",
      "do_not_copy": "Do not edit the existing ds5319-swd object. Do not redraw sample-01-swd-vectors.svg."
    },
    {
      "id": "ds5319-clock",
      "claim": "LQFP48 pin 5 is PD0-OSC_IN and pin 6 is PD1-OSC_OUT. Both pins exist on this package and carry the 8 MHz HSE.",
      "do_not_copy": "Do not edit the existing ds5319-clock object. Do not redraw sample-02-clock-tree.svg. Do not say these pins are absent."
    },
    {
      "id": "rm0008-rcc",
      "claim": "With the PLL at 72 MHz, USBPRE=0 divides by 1.5 and yields 48 MHz. USBPRE=1 leaves the USB clock at 72 MHz.",
      "do_not_copy": "Do not edit the existing rm0008-rcc object. Do not redraw the chapter 02 clock tree."
    },
    {
      "id": "ds5319-i2c",
      "claim": "Pin 45 PB8 and pin 46 PB9 are also the I2C1 remap. Chapter 13 does not draw CAN and I2C active on that pair at the same time.",
      "do_not_copy": "Do not edit the existing ds5319-i2c object. Do not redraw sample-07-i2c-addr.svg."
    },
    {
      "id": "project-examples",
      "claim": "examples/iap-bootloader sizes the application as 0xB800. examples/can-bxcan uses prescaler 9, shifts a standard ID left by 5 into FilterIdHigh, asks for 120 ohm at each end, and recovers with 128 times 11 recessive bits when ABOM is on. examples/usb-cdc uses an 18-byte device descriptor, a 67-byte configuration set, and VID/PID 0x1209/0x0001. examples/freertos-task uses stacks of 128, 192, and 256 words, task priorities 1 and 2, EXTI priority 5, and TIM4 as the HAL time base.",
      "do_not_copy": "Do not edit the existing project-examples object. Do not open a new example id. Do not paste example functions. Do not change the example trees."
    },
    {
      "id": "rm0090",
      "claim": "F4 sector sizes and F4 bxCAN are sentences that become true only after changing family. They are void as a drop-in for this C8.",
      "do_not_copy": "Do not edit the existing rm0090 object. Do not use it to redraw the C8 page map."
    }
  ],
  "absorb": [
    {
      "id": "rm0008-flash",
      "chapters": ["12"],
      "title_zh": "RM0008 Rev 21 中容量闪存的页、半字和两把钥匙",
      "title_en": "RM0008 Rev 21 medium-density Flash pages, half-words, and the two keys",
      "authority_zh": "ST 官方参考手册",
      "authority_en": "ST reference manual",
      "url": "https://www.st.com/resource/en/reference_manual/rm0008-stm32f101xx-stm32f102xx-stm32f103xx-advanced-arm-based-32-bit-mcus-stmicroelectronics.pdf",
      "snapshot": "RM0008 Rev 21, February 2021. Default chapter 3, embedded Flash. Medium-density parts erase by 1 KB pages and program by half-word. Unlock FLASH_KEYR by writing 0x45670123 and then 0xCDEF89AB. The high-density 2 KB page is void on STM32F103C8T6. An erased half-word reads back 0xFFFF. Programming can change a 1 only to a 0. If the printed chapter title is not the embedded Flash chapter, replace this section number with the printed chapter. The claim does not change. This snapshot does not include a 20-40 ms erase time and does not call 0xAA the unprotected key.",
      "license": "ST document terms (link and restated facts only; the manual is not redistributed)",
      "license_class": "ST-facts-restated",
      "section": "3",
      "do_not_copy": true,
      "points": [
        "Medium-density STM32F103 erases 1 KB pages. The high-density 2 KB page is void on STM32F103C8T6",
        "Programming granularity is a half-word. An erased half-word reads 0xFFFF. Byte programming is void on this part",
        "Unlock writes 0x45670123 and then 0xCDEF89AB. The reverse order leaves LOCK set"
      ]
    },
    {
      "id": "rm0008-can",
      "chapters": ["13"],
      "title_zh": "RM0008 Rev 21 bxCAN 的位时间、总线关闭和过滤器",
      "title_en": "RM0008 Rev 21 bxCAN bit time, bus-off, and filters",
      "authority_zh": "ST 官方参考手册",
      "authority_en": "ST reference manual",
      "url": "https://www.st.com/resource/en/reference_manual/rm0008-stm32f101xx-stm32f102xx-stm32f103xx-advanced-arm-based-32-bit-mcus-stmicroelectronics.pdf",
      "snapshot": "RM0008 Rev 21, February 2021. Default chapter 21, bxCAN. Bit time is one synchronization quantum plus BS1 plus BS2. The CAN_BTR prescaler field uses the printed bits. A transmit error counter of 256 enters bus-off. Recovery requires 128 occurrences of 11 consecutive recessive bits. There are 14 filter banks and 2 receive FIFOs. In a 32-bit filter the standard identifier occupies the printed bits; this repository places it in FilterIdHigh shifted left by 5. Remap encodings use the printed values: one encoding reaches PB8/PB9 and another reaches PD0/PD1. If the printed chapter or bit fields differ, use the printed text. 500 kbit/s remains prescaler 9 and 8 time quanta. This snapshot does not include a CAN base address and does not call 450 kbit/s the working point.",
      "license": "ST document terms (link and restated facts only; the manual is not redistributed)",
      "license_class": "ST-facts-restated",
      "section": "21",
      "do_not_copy": true,
      "points": [
        "At 36 MHz, prescaler 9 and 8 time quanta is 500 kbit/s. Prescaler 8 and 10 time quanta is 450 kbit/s",
        "A transmit error counter of 256 enters bus-off. Recovery takes 128 times 11 recessive bits",
        "14 filter banks and 2 receive FIFOs. Do not invent a CAN base address"
      ]
    },
    {
      "id": "ds5319-usbcan",
      "chapters": ["13", "14"],
      "title_zh": "DS5319 Rev 20 表 5 的 USB 与 CAN 脚",
      "title_en": "DS5319 Rev 20 Table 5 USB and CAN pins",
      "authority_zh": "ST 官方数据手册",
      "authority_en": "ST datasheet",
      "url": "https://www.st.com/resource/en/datasheet/stm32f103c8.pdf",
      "snapshot": "DS5319 Rev 20, July 2025, Table 5 LQFP48 column. Pin 31 is already PA10 and pin 34 is already PA13. The default pins between them are pin 32 PA11 and pin 33 PA12. PA11 alternate functions include USB_DM and CAN_RX. PA12 alternate functions include USB_DP and CAN_TX. Pin 45 PB8 and pin 46 PB9 include a CAN remap. Pin 5 and pin 6 are the PD0 and PD1 already recorded by ds5319-clock; the package has both pins. If the printed pin numbers differ, use the printed numbers and the printed alternate-function column. An on-chip pull-up resistance is copied into this snapshot only when this datasheet prints the ohms. This snapshot does not trace the package drawing and does not assign a transceiver pinout.",
      "license": "ST document terms (link and restated facts only; the manual is not redistributed)",
      "license_class": "ST-facts-restated",
      "section": "Table 5",
      "do_not_copy": true,
      "points": [
        "Default pin 32 is PA11 and default pin 33 is PA12. PA11 includes USB_DM and CAN_RX. PA12 includes USB_DP and CAN_TX",
        "Pin 45 PB8 and pin 46 PB9 include the CAN remap",
        "Pin 5 PD0 and pin 6 PD1 exist on LQFP48. They are the HSE pins"
      ]
    },
    {
      "id": "rm0008-usb",
      "chapters": ["13", "14"],
      "title_zh": "RM0008 Rev 21 USB 全速设备与共享中断",
      "title_en": "RM0008 Rev 21 USB full-speed device and the shared interrupt",
      "authority_zh": "ST 官方参考手册",
      "authority_en": "ST reference manual",
      "url": "https://www.st.com/resource/en/reference_manual/rm0008-stm32f101xx-stm32f102xx-stm32f103xx-advanced-arm-based-32-bit-mcus-stmicroelectronics.pdf",
      "snapshot": "RM0008 Rev 21, February 2021. Default chapter 23, USB device. On STM32F103 this block is a full-speed device, not a host. The USB clock must be 48 MHz. The interrupt shared with bxCAN receive uses the printed vector name. The default name written here is USB_LP_CAN1_RX0. An on-chip D+ pull-up is added here only if the manual prints it, together with the printed resistance. If no resistance is printed, do not invent a kiloohm. If the printed chapter title or vector name differs, use the printed text. The 48 MHz claim and the device-not-host claim do not change. 480 Mbit/s is void on this part.",
      "license": "ST document terms (link and restated facts only; the manual is not redistributed)",
      "license_class": "ST-facts-restated",
      "section": "23",
      "do_not_copy": true,
      "points": [
        "STM32F103 USB is a full-speed device, not a host, and not 480 Mbit/s",
        "The USB clock must be 48 MHz",
        "The default shared vector name is USB_LP_CAN1_RX0. Replace the name only with the printed vector name"
      ]
    },
    {
      "id": "freertos-syscall",
      "chapters": ["15"],
      "title_zh": "FreeRTOS Kernel V11.3.2 的 FromISR 移位、字栈和互斥量",
      "title_en": "FreeRTOS Kernel V11.3.2 FromISR shift, word stacks, and mutexes",
      "authority_zh": "FreeRTOS 内核",
      "authority_en": "FreeRTOS kernel",
      "url": "https://github.com/FreeRTOS/FreeRTOS-Kernel/releases/tag/V11.3.2",
      "snapshot": "FreeRTOS Kernel V11.3.2, the same release tag as freertos-1132. MIT. The Cortex-M port shifts the library priority left by (8 minus the number of priority bits) before the value used with BASEPRI. With 4 priority bits and library priority 5, the shifted value is 0x50. An interrupt with a numerically smaller priority must not call FromISR. A numerically larger task priority runs first. The xTaskCreate depth is in words. heap_4 coalesces adjacent free blocks. A mutex has priority inheritance and a binary semaphore does not. If a demo in this tag prints a library priority other than 5, record the printed formula here. This repository's EXTI priority stays 5. This snapshot does not include a 17.2 percent budget.",
      "license": "MIT",
      "license_class": "MIT",
      "section": "V11.3.2",
      "do_not_copy": true,
      "points": [
        "With 4 priority bits, 5 shifted left by 4 is 0x50. A numerically smaller interrupt must not call FromISR",
        "A numerically larger task priority runs first. xTaskCreate depth is in words",
        "A mutex has priority inheritance. A binary semaphore does not. heap_4 coalesces adjacent free blocks"
      ]
    }
  ]
}
```

- [ ] **Step 2: 写许可门测试**

保存为 `stm32-book/tests/test_batch5_sources.py`：

```python
#!/usr/bin/env python3
"""License gate for chapters 12, 13, 14, and 15. The manifest is updated later."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_LIST = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch5-12-13-14-15-source-list.json"
LOCK = ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch5-12-13-14-15-lock.json"
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
    "rm0008-flash",
    "rm0008-can",
    "ds5319-usbcan",
    "rm0008-usb",
    "freertos-syscall",
]
REUSED = [
    "pm0075-rdp",
    "pm0056-vector",
    "ds5319-swd",
    "ds5319-clock",
    "rm0008-rcc",
    "ds5319-i2c",
    "project-examples",
    "rm0090",
]


class Batch5SourceListTests(unittest.TestCase):
    def test_lock_keeps_chapters_12_13_14_15(self) -> None:
        lock = json.loads(LOCK.read_text(encoding="utf-8"))
        self.assertEqual(["12", "13", "14", "15"], lock["chapters"])
        self.assertTrue(lock["four_blocks_absent"])
        self.assertTrue(lock["old_pitfall_heading_present"])
        self.assertEqual(40, len(lock["baseline"]))
        self.assertEqual("2026-10-25-classic-encyclopedia-batch5-12-13-14-15", lock["rubric"])
        expected = (
            ("12", "docs/12-Flash与IAP升级.md", "docs/en/12-flash-iap.md", "## ⚠️ Pitfalls and troubleshooting"),
            ("13", "docs/13-CAN总线.md", "docs/en/13-can.md", "## ⚠️ Pitfalls"),
            ("14", "docs/14-USB.md", "docs/en/14-usb.md", "## ⚠️ Pitfalls"),
            ("15", "docs/15-FreeRTOS入门.md", "docs/en/15-freertos.md", "## ⚠️ Pitfalls and troubleshooting"),
        )
        for prefix, zh_name, en_name, en_old in expected:
            row = lock["files"][prefix]
            self.assertEqual(zh_name, row["zh"])
            self.assertEqual(en_name, row["en"])
            self.assertFalse(row["zh_four_blocks"])
            self.assertFalse(row["en_four_blocks"])
            self.assertTrue(row["zh_old_pitfall"])
            self.assertTrue(row["en_old_pitfall"])
            self.assertEqual(en_old, row["en_old_heading"])

    def test_source_list_keeps_the_license_gate(self) -> None:
        payload = json.loads(SOURCE_LIST.read_text(encoding="utf-8"))
        self.assertEqual(["12", "13", "14", "15"], payload["chapters"])
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
        self.assertEqual("3", by_id["rm0008-flash"]["section"])
        self.assertEqual("21", by_id["rm0008-can"]["section"])
        self.assertEqual("Table 5", by_id["ds5319-usbcan"]["section"])
        self.assertEqual("23", by_id["rm0008-usb"]["section"])
        self.assertEqual("V11.3.2", by_id["freertos-syscall"]["section"])
        self.assertEqual("MIT", by_id["freertos-syscall"]["license"])
        self.assertEqual("MIT", by_id["freertos-syscall"]["license_class"])
        flash = by_id["rm0008-flash"]["snapshot"]
        self.assertIn("0x45670123", flash)
        self.assertIn("0xCDEF89AB", flash)
        self.assertIn("1 KB", flash)
        self.assertNotIn("20-40 ms", flash)
        self.assertNotIn("0xAA", flash)
        can = by_id["rm0008-can"]["snapshot"]
        self.assertIn("256", can)
        self.assertIn("128", can)
        self.assertNotIn("0x40006400", can)
        usb = by_id["rm0008-usb"]["snapshot"]
        self.assertIn("USB_LP_CAN1_RX0", usb)
        self.assertIn("48 MHz", usb)
        self.assertNotIn("480 Mbit/s is the", usb)
        pins = by_id["ds5319-usbcan"]["snapshot"]
        self.assertIn("pin 32", pins)
        self.assertIn("pin 45", pins)
        self.assertNotIn("absent", pins.lower())
        rtos = by_id["freertos-syscall"]["snapshot"]
        self.assertIn("0x50", rtos)
        self.assertNotIn("17.2", rtos)
        self.assertNotIn("167 ns", rtos)
        reused = [item["id"] for item in payload["reuse_existing"]]
        self.assertEqual(REUSED, reused)
        for banned_id in (
            "usb20",
            "freertos-priority",
            "freertos-1132",
            "an2606",
            "an3965",
            "pm0056",
            "pm0056-nvic",
        ):
            self.assertNotIn(banned_id, ids)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: 运行测试，并只核对会改 snapshot 的六处**

Run: `python3 stm32-book/tests/test_batch5_sources.py -v`

Expected: OK，两条测试都通过。清单已经在这一任务的工作区里，所以这一步不是 `FileNotFoundError`。若失败，改清单去满足上面的断言，不要放宽 `ABSORB`，也不要删掉测试来制造一次红色。不要追加第六个 id。

锁定文件那一条若失败，先回到 Task 1。不要改测试去迁就一份章号不对的锁。

然后打开 Step 开头的三个 URL，只核对下面六处。印出的句子还在，清单不动。

脚号：读 DS5319 Rev 20 表 5 的 LQFP48 列。默认第 32 脚 PA11、第 33 脚 PA12，第 45 脚 PB8、第 46 脚 PB9，第 5 脚 PD0、第 6 脚 PD1。印出的脚号不同，把 `ds5319-usbcan` 的 snapshot 改成印出的脚号，信号名按印出的复用列，并在实施 PR 里写明。不沿用一份没核对过的脚号去否定表 5。

片内上拉：在 RM0008 和 DS5319 里找片内 D+ 上拉的阻值。没印出阻值，两份 snapshot 都不写千欧，图上仍按罗盘标 1.5 kΩ。印出了阻值，把印出的欧姆数写进印出它的那一个 id（`rm0008-usb` 或 `ds5319-usbcan`），不新开 id。印出的不是 1.5 kΩ，片内那只用印出的数，罗盘的 1.5 kΩ 仍是板级上拉的主张。

USB 章号和向量名：默认第 23 章，向量名 `USB_LP_CAN1_RX0`。印出的标题或名字不同，改 `rm0008-usb` 的 `section` 和 snapshot。48 MHz 和「设备不是主机」不变。

CAN 章号和重映射：默认第 21 章。印出的章号或重映射编码不同，改 `rm0008-can` 的 `section` 和 snapshot。500 kbit/s 仍是预分频 9 和 8 个时间份额。不编基址。

过滤器的 5 位：默认与例程一致，标准 ID 放在 `FilterIdHigh`，左移 5。RM0008 印出的位若对不上这 5 位，把印出的位写进 `rm0008-can` 的 snapshot，并在实施 PR 里写明例程的 5 位对应高半字的哪一段。不把 21 再左移进 `FilterIdHigh`。

FreeRTOS 的库优先级：默认左移 `(8 − 4)`，本仓库 EXTI 用 5，得到 `0x50`。V11.3.2 演示工程印出的库优先级若不是 5，把 `freertos-syscall` 的 snapshot 改成印出的公式。例程的 5 不改。不把 17.2% 写进 snapshot。

无论哪一处，都不要改 `license_class`，不要改另外几个 id 的 `points`，不要新增第六个 id。

- [ ] **Step 4: 再跑测试并提交**

Run: `python3 stm32-book/tests/test_batch5_sources.py -v`

Expected: OK。

```bash
git add docs/superpowers/plans/2026-10-25-batch5-12-13-14-15-source-list.json stm32-book/tests/test_batch5_sources.py
git commit -m "docs: 钉上 12、13、14、15 的许可门"
```

不要在这一笔里改章节正文。不要改已有来源对象。

### Task 3: Static key figures

**Files:**
- Modify: `tools/gen_sample_figures.py`（只追加函数，并在 `main()` 里多保存四张。不改 `boot_state`、`gpio_led`、`exception_stack`、`uart_frame`、`clock_tree`、`pwm_1khz`、`spi_jedec`、`adc_sample`、`swd_vectors`、`i2c_addr`、`dma_cndtr`、`iwdg_1s`、`_credit`）
- Create: `assets/diagrams/sample-12-iap-map.svg`
- Create: `assets/diagrams/sample-13-can-bit.svg`
- Create: `assets/diagrams/sample-14-usb-enum.svg`
- Create: `assets/diagrams/sample-15-rtos-prio.svg`
- Modify: `assets/README.md`（开头的生成命令，第一节里四张旧动画的说明，第四节表的末尾）
- Create: `stm32-book/tests/test_batch5_chapters.py`
- Test: `stm32-book/tests/test_batch5_chapters.py`

**Interfaces:**
- Consumes: Task 2 清单里的订货号、脚位和寄存器名。已有的 `_credit(canvas, note)`。
- Produces: `iap_map() -> Svg`、`can_bit() -> Svg`、`usb_enum() -> Svg`、`rtos_prio() -> Svg`。四张 SVG 不含 `<animate`、`@keyframes`、`animation:`，不含「矢量动画」，不含「实拍」，含「自绘」。每张都小于 60 KB。默认不产生 `sample-12-iap-vectors.svg`。

`sample-12-iap-map.svg` 的文本含 `STM32F103C8T6`、`LQFP48`、`0x08000000`、`0x08004000`、`0x08004800`、`0x08004804`、`0x0800FC00`、`0x08010000`、`0xB800`、`0x45670123`、`0xCDEF89AB`、`0x0801FC00`、`LOCK`、`VTOR`、`MSP`、`Reset_Handler`、`1 KB`、`64 KB`、`medium-density`。不含 `0x1FFFF000`。

`sample-13-can-bit.svg` 的文本含 `STM32F103C8T6`、`36 MHz`、`pin 45`、`PB8`、`pin 46`、`PB9`、`250 ns`、`2 us`、`500 kbit/s`、`75%`、`prescaler 9`、`450 kbit/s`、`70%`、`120`、`CANH`、`CANL`、`pin 32`、`PA11`、`pin 5`、`PD0`、`pin 6`、`PD1`。不含 `absent`。

`sample-14-usb-enum.svg` 的文本含 `STM32F103C8T6`、`pin 32`、`PA11`、`DM`、`pin 33`、`PA12`、`DP`、`1.5`、`48 MHz`、`USBPRE = 0`、`USBPRE = 1`、`72 MHz`、`18`、`67`、`0x1209`、`0x0001`、`64`、`100 mA`、`1023`、`0x0483`。

`sample-15-rtos-prio.svg` 的文本含 `STM32F103C8T6`、`1 ms`、`TIM4`、`128 words`、`512 bytes`、`0x50`、`priority 2`、`priority 1`、`EXTI0`、`configASSERT`、`SysTick`。不含 `167 ns`，不含 `17.2`。

- [ ] **Step 1: 写会失败的主图测试**

保存为 `stm32-book/tests/test_batch5_chapters.py`：

```python
#!/usr/bin/env python3
"""Checks for thickened chapters 12, 13, 14, and 15 and their static figures."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIAGRAMS = ROOT / "assets" / "diagrams"
IAP = DIAGRAMS / "sample-12-iap-map.svg"
CAN = DIAGRAMS / "sample-13-can-bit.svg"
USB = DIAGRAMS / "sample-14-usb-enum.svg"
RTOS = DIAGRAMS / "sample-15-rtos-prio.svg"


class Batch5FigureTests(unittest.TestCase):
    def test_key_figures_are_static_and_under_60_kib(self) -> None:
        for path, tokens in (
            (
                IAP,
                (
                    "STM32F103C8T6",
                    "LQFP48",
                    "0x08000000",
                    "0x08004000",
                    "0x08004800",
                    "0x08004804",
                    "0x0800FC00",
                    "0x08010000",
                    "0xB800",
                    "0x45670123",
                    "0xCDEF89AB",
                    "0x0801FC00",
                    "LOCK",
                    "VTOR",
                    "MSP",
                    "Reset_Handler",
                    "1 KB",
                    "64 KB",
                    "medium-density",
                ),
            ),
            (
                CAN,
                (
                    "STM32F103C8T6",
                    "36 MHz",
                    "pin 45",
                    "PB8",
                    "pin 46",
                    "PB9",
                    "250 ns",
                    "2 us",
                    "500 kbit/s",
                    "75%",
                    "prescaler 9",
                    "450 kbit/s",
                    "70%",
                    "120",
                    "CANH",
                    "CANL",
                    "pin 32",
                    "PA11",
                    "pin 5",
                    "PD0",
                    "pin 6",
                    "PD1",
                ),
            ),
            (
                USB,
                (
                    "STM32F103C8T6",
                    "pin 32",
                    "PA11",
                    "DM",
                    "pin 33",
                    "PA12",
                    "DP",
                    "1.5",
                    "48 MHz",
                    "USBPRE = 0",
                    "USBPRE = 1",
                    "72 MHz",
                    "18",
                    "67",
                    "0x1209",
                    "0x0001",
                    "64",
                    "100 mA",
                    "1023",
                    "0x0483",
                ),
            ),
            (
                RTOS,
                (
                    "STM32F103C8T6",
                    "1 ms",
                    "TIM4",
                    "128 words",
                    "512 bytes",
                    "0x50",
                    "priority 2",
                    "priority 1",
                    "EXTI0",
                    "configASSERT",
                    "SysTick",
                ),
            ),
        ):
            raw = path.read_text(encoding="utf-8")
            self.assertLess(path.stat().st_size, 60 * 1024, path.name)
            for banned in ("<animate", "@keyframes", "animation:", "矢量动画", "实拍"):
                self.assertNotIn(banned, raw)
            for token in tokens:
                self.assertIn(token, raw)
            self.assertIn("自绘", raw)
            self.assertNotIn("Svg.footer", raw)
        iap = IAP.read_text(encoding="utf-8")
        self.assertNotIn("0x1FFFF000", iap)
        can = CAN.read_text(encoding="utf-8")
        self.assertNotIn("absent", can.lower())
        rtos = RTOS.read_text(encoding="utf-8")
        self.assertNotIn("167 ns", rtos)
        self.assertNotIn("17.2", rtos)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试，确认它因为文件不存在而失败**

Run: `python3 stm32-book/tests/test_batch5_chapters.py -v`

Expected: FAIL，`sample-12-iap-map.svg` 不存在（`FileNotFoundError`）。

- [ ] **Step 3: 追加四个生成函数并写出 SVG**

在 `tools/gen_sample_figures.py` 的 `iwdg_1s()` 之后、`main()` 之前插入下面四个函数。不要改已有十二个函数，也不要改 `_credit`。

```python
def iap_map() -> Svg:
    canvas = Svg(
        960,
        980,
        "中容量 1 KB 页；APP 从 0x08004800 起，长度 0xB800；跳转要装入第 0 字和第 1 字",
        "STM32F103C8T6 LQFP48 · RM0008 Rev 21 chapter 3",
    )
    canvas.header(tag="12", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  LQFP48  medium-density  64 KB", size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "1 KB pages. page 0 at 0x08000000. page 63 at 0x0800FC00", size=14, fill=T.CYAN)
    canvas.text(40, 138, "map ends before 0x08010000. 16 KB + 2 KB + 46 KB = 64 KB", size=14, fill=T.AMBER)
    canvas.text(40, 170, "正常路径  KEY1 then KEY2, then a half-word, then the two words", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 184, 880, 170, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 214, "write 0x45670123, then 0xCDEF89AB. LOCK clears", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 240, "program a half-word on an even address inside the APP", size=14, fill=T.GREEN)
    canvas.text(56, 266, "Bootloader 0x08000000, 16 KB, 16 pages, ends at 0x08004000", size=14, fill=T.TEXT)
    canvas.text(56, 292, "parameters 0x08004000, 2 KB, 2 pages, ends at 0x08004800", size=14, fill=T.TEXT)
    canvas.text(56, 318, "APP 0x08004800, 46 KB, 0xB800, ends at 0x08010000", size=14, fill=T.AMBER)
    canvas.text(56, 340, "MSP at 0x08004800. Reset_Handler at 0x08004804. VTOR = 0x08004800", size=13, fill=T.MUTED)
    canvas.text(40, 380, "失败路径  reversed keys, a last page past 64 KB, or VTOR left at 0", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 394, 880, 130, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 424, "KEY2 before KEY1 leaves LOCK set. The erase returns an error", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 450, "0x0801FC00 is outside this 64 KB", size=14, fill=T.RED)
    canvas.text(56, 476, "VTOR left at 0 still vectors interrupts into the bootloader", size=14, fill=T.AMBER)
    canvas.text(56, 502, "an erased half-word reads 0xFFFF. programming only turns 1 into 0", size=13, fill=T.MUTED)
    canvas.rect(40, 544, 880, 140, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 574, "旁注  byte programming is void on this C8", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 600, "0xA5 stays in chapter 01. This figure does not draw option bytes", size=14, fill=T.TEXT)
    canvas.text(56, 626, "USART on pin 30 PA9 and pin 31 PA10 is a side note, not a frame", size=14, fill=T.AMBER)
    canvas.text(56, 652, "do not draw system memory on this user-Flash map", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。页和钥匙来自 RM0008 Rev 21 第 3 章；两字来自 PM0056。")
    return canvas


def can_bit() -> Svg:
    canvas = Svg(
        960,
        980,
        "36 MHz 下预分频 9、8 个时间份额是 500 kbit/s；预分频 8 和 10 个时间份额是 450 kbit/s；工作脚是第 45 脚和第 46 脚",
        "STM32F103C8T6 LQFP48 · RM0008 Rev 21 bxCAN",
    )
    canvas.header(tag="13", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  LQFP48  CAN1 on APB1  36 MHz", size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "pin 45 PB8 = CAN_RX    pin 46 PB9 = CAN_TX", size=14, fill=T.CYAN)
    canvas.text(40, 138, "MCU pins enter the transceiver. 120 ohm sits on CANH and CANL, at each end", size=14, fill=T.AMBER)
    canvas.text(40, 170, "正常路径  prescaler 9, eight quanta, 2 us, 500 kbit/s", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 184, 880, 160, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 214, "Tq = 250 ns. SYNC 1 + BS1 5 + BS2 2 = 8", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 240, "sample at 1.5 us, 75%. SJW = 1", size=14, fill=T.GREEN)
    canvas.text(56, 266, "8 x 250 ns = 2 us", size=14, fill=T.TEXT)
    canvas.text(56, 292, "the resistor is not tied to PB8 or PB9", size=14, fill=T.AMBER)
    canvas.text(56, 318, "two 120 ohm parts in parallel are a 60 ohm DC load, not a cable impedance", size=13, fill=T.MUTED)
    canvas.text(40, 370, "失败路径  prescaler 8, BS1 6, BS2 3, ten quanta, 450 kbit/s", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 384, 880, 120, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 414, "36e6 / (8 x 10) = 450 kbit/s. sample point 70%", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 440, "the bit is no longer 2 us", size=14, fill=T.RED)
    canvas.text(56, 466, "1 Mbit/s stays off this figure", size=14, fill=T.AMBER)
    canvas.rect(40, 524, 880, 150, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 554, "旁注  pin 32 PA11 and pin 33 PA12 stay with USB", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 580, "pin 5 PD0 and pin 6 PD1 exist. Remapping CAN there stops the HSE", size=14, fill=T.TEXT)
    canvas.text(56, 606, "pin 45 and pin 46 are not drawn as I2C at the same time", size=14, fill=T.AMBER)
    canvas.text(56, 632, "bus-off at 256 and 128 x 11 recessive bits stay in the table, not as a second waveform", size=13, fill=T.MUTED)
    canvas.text(56, 656, "do not draw the 4.7 kilohm I2C pull-ups on this figure", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。位时间来自 RM0008 Rev 21 bxCAN；脚位来自 DS5319 Rev 20 表 5。")
    return canvas


def usb_enum() -> Svg:
    canvas = Svg(
        960,
        980,
        "全速要 48 MHz；D+ 上拉在第 33 脚；描述符是 18 字节设备加 67 字节配置集合，VID/PID 是 0x1209/0x0001",
        "STM32F103C8T6 LQFP48 · RM0008 Rev 21 USB device",
    )
    canvas.header(tag="14", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  LQFP48  USB device, not a host", size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "pin 32 PA11 = DM    pin 33 PA12 = DP", size=14, fill=T.CYAN)
    canvas.text(40, 138, "1.5 kilohm from 3.3 V to DP. USBPRE = 0. clock 48 MHz", size=14, fill=T.AMBER)
    canvas.text(40, 170, "正常路径  the host sees D+ pulled up", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 184, 880, 170, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 214, "device descriptor 18 bytes. bMaxPacketSize0 = 64", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 240, "VID/PID 0x1209/0x0001", size=14, fill=T.GREEN)
    canvas.text(56, 266, "configuration set length 67. wTotalLength 0x0043", size=14, fill=T.TEXT)
    canvas.text(56, 292, "bMaxPower 0x32 = 100 mA", size=14, fill=T.AMBER)
    canvas.text(56, 318, "full-speed bulk and interrupt ceiling is 64. notification endpoint 8 is allowed", size=13, fill=T.MUTED)
    canvas.text(40, 380, "失败路径  USBPRE = 1, the USB clock becomes 72 MHz", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 394, 880, 110, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 424, "the host fails while reading the descriptor", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 450, "72 / 1.5 is not applied", size=14, fill=T.RED)
    canvas.text(56, 476, "480 Mbit/s is void on this part", size=14, fill=T.AMBER)
    canvas.rect(40, 524, 880, 150, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 554, "旁注  1.5 kilohm tied to DM is not this full-speed device", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 580, "a bulk or interrupt wMaxPacketSize of 1023 is the wrong class", size=14, fill=T.TEXT)
    canvas.text(56, 606, "0x0483/0x5740 is not this repository descriptor", size=14, fill=T.AMBER)
    canvas.text(56, 632, "do not draw a CAN transceiver or ULPI on this figure", size=13, fill=T.MUTED)
    canvas.text(56, 656, "shared vector stays a side note: see the source card", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。48 MHz 来自已冻结的 USBPRE；脚位来自 DS5319 Rev 20 表 5；长度来自本仓库 usb-cdc。")
    return canvas


def rtos_prio() -> Svg:
    canvas = Svg(
        960,
        960,
        "一个 tick 是 1 ms；任务优先级 2 先于 1；128 字是 512 字节；FromISR 的数值优先级要大于等于 5",
        "STM32F103C8T6 · FreeRTOS Kernel V11.3.2",
    )
    canvas.header(tag="15", tag_color=T.CYAN)
    canvas.text(40, 86, "STM32F103C8T6  Cortex-M3  no FPU  GROUP_4", size=16, fill=T.TEXT, weight="700")
    canvas.text(40, 112, "SysTick tick = 1 ms. HAL time base = TIM4, not SysTick", size=14, fill=T.CYAN)
    canvas.text(40, 138, "5 << 4 = 0x50. EXTI0 priority 5 may call FromISR", size=14, fill=T.AMBER)
    canvas.text(40, 170, "正常路径  task priority 2 runs, task priority 1 waits", size=16, fill=T.GREEN, weight="700")
    canvas.rect(40, 184, 880, 160, fill=T.PANEL, stroke=T.GREEN, rx=8)
    canvas.text(56, 214, "KEY is priority 2. LED and UART are priority 1", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 240, "LED stack 128 words = 512 bytes", size=14, fill=T.GREEN)
    canvas.text(56, 266, "EXTI0 preemption priority 5 may xQueueSendFromISR", size=14, fill=T.TEXT)
    canvas.text(56, 292, "the numeric task order is the opposite of NVIC", size=14, fill=T.AMBER)
    canvas.text(56, 318, "configTICK_RATE_HZ = 1000", size=13, fill=T.MUTED)
    canvas.text(40, 370, "失败路径  the same EXTI preemption priority is 0", size=16, fill=T.RED, weight="700")
    canvas.rect(40, 384, 880, 120, fill=T.PANEL, stroke=T.RED, rx=8)
    canvas.text(56, 414, "calling FromISR stops in configASSERT", size=15, fill=T.TEXT, weight="700")
    canvas.text(56, 440, "priority number 4 is also too urgent", size=14, fill=T.RED)
    canvas.text(56, 466, "NVIC number 0 is the most urgent interrupt", size=14, fill=T.AMBER)
    canvas.rect(40, 524, 880, 140, fill=T.BG2, stroke=T.VIOLET, rx=8)
    canvas.text(56, 554, "旁注  128 words is not 128 bytes", size=15, fill=T.VIOLET, weight="700")
    canvas.text(56, 580, "HAL left on SysTick makes HAL_Delay stick", size=14, fill=T.TEXT)
    canvas.text(56, 606, "task priority 1 is not ahead of task priority 2", size=14, fill=T.AMBER)
    canvas.text(56, 632, "do not draw the 8-register exception entry on this figure", size=13, fill=T.MUTED)
    _credit(canvas, "自绘。移位来自 FreeRTOS Kernel V11.3.2；栈和 TIM4 来自本仓库 freertos-task。")
    return canvas
```

把 `main()` 换成：

```python
def main() -> None:
    out_dir = os.path.join(ROOT, "assets", "diagrams")
    os.makedirs(out_dir, exist_ok=True)
    boot_state().save(os.path.join(out_dir, "sample-00-boot-state.svg"))
    gpio_led().save(os.path.join(out_dir, "sample-03-gpio-led.svg"))
    exception_stack().save(os.path.join(out_dir, "sample-04-exception-stack.svg"))
    uart_frame().save(os.path.join(out_dir, "sample-06-uart-frame.svg"))
    clock_tree().save(os.path.join(out_dir, "sample-02-clock-tree.svg"))
    pwm_1khz().save(os.path.join(out_dir, "sample-05-pwm-1khz.svg"))
    spi_jedec().save(os.path.join(out_dir, "sample-08-spi-jedec.svg"))
    adc_sample().save(os.path.join(out_dir, "sample-09-adc-sar.svg"))
    swd_vectors().save(os.path.join(out_dir, "sample-01-swd-vectors.svg"))
    i2c_addr().save(os.path.join(out_dir, "sample-07-i2c-addr.svg"))
    dma_cndtr().save(os.path.join(out_dir, "sample-10-dma-cndtr.svg"))
    iwdg_1s().save(os.path.join(out_dir, "sample-11-iwdg-1s.svg"))
    iap_map().save(os.path.join(out_dir, "sample-12-iap-map.svg"))
    can_bit().save(os.path.join(out_dir, "sample-13-can-bit.svg"))
    usb_enum().save(os.path.join(out_dir, "sample-14-usb-enum.svg"))
    rtos_prio().save(os.path.join(out_dir, "sample-15-rtos-prio.svg"))
```

Run: `python3 tools/gen_sample_figures.py`

Expected: 退出码 0。四张新 SVG 出现在 `assets/diagrams/`。`sample-12-iap-map.svg` 小于 60 KB 时，不要另写 `sample-12-iap-vectors.svg`。它达到或超过 60 KB 时，把两字那一块拆进 `iap_vectors() -> Svg`，文件名 `sample-12-iap-vectors.svg`。第一张仍是地图，仍含 `0x08000000`、`0x08004800`、`0xB800`、`0x45670123`、`0xCDEF89AB`、`0x0801FC00`。第二张含 `MSP`、`Reset_Handler`、`0x08004804`、`VTOR`。两张都用 `_credit()`，都不调用 `Svg.footer()`。`main()` 多保存这一张。拆开仍超过时，在实施 PR 里写出字节数和原因，不把图画回简笔，也不把 60 KB 改成仓库新默认值。第 13、14、15 章不另起第二张文件名。若已有十二张 `sample-00` 到 `sample-11` 出现内容 diff，说明旧函数被改过，先还原那十二个函数再生成。不要把这十二张旧图的改动提交进来。

在 `assets/README.md` 开头的生成命令里，把

```bash
python3 tools/gen_sample_figures.py   # 第 00、01、02、03、04、05、06、07、08、09、10、11 章的静态主图
```

换成

```bash
python3 tools/gen_sample_figures.py   # 第 00 到第 15 章的静态主图
```

第一节表格里这四行：

```markdown
| `flash-iap.svg` | IAP 在线升级：Bootloader + APP 双区跳转 | 12 |
| `can-arbitration.svg` | CAN 非破坏性仲裁与位填充 | 13 |
| `usb-enumeration.svg` | USB 设备枚举：复位 → 描述符 → 配置 | 14 |
| `freertos-scheduler.svg` | FreeRTOS 任务状态迁移与抢占式调度 | 15 |
```

换成：

```markdown
| `flash-iap.svg` | 辅图：IAP 双区跳转。文件不重画。页边界、两把钥匙和两字在静态主图上 | 12 |
| `can-arbitration.svg` | 辅图：CAN 仲裁与位填充。文件不重画。500 kbit/s 和 450 kbit/s 在静态主图上 | 13 |
| `usb-enumeration.svg` | 辅图：USB 枚举。文件不重画。48 MHz 和描述符长度在静态主图上 | 14 |
| `freertos-scheduler.svg` | 辅图：任务状态。文件不重画。1 ms、优先级和字栈在静态主图上 | 15 |
```

第四节表格末尾追加这四行。只有拆出第二张时才加第五行：

```markdown
| `sample-12-iap-map.svg` | 第 12 章静态主图：64 KB 中容量地图、先 KEY1 后 KEY2，以及钥匙反序、0x0801FC00 和 VTOR 仍为 0。由 `tools/gen_sample_figures.py` 生成 |
| `sample-13-can-bit.svg` | 第 13 章静态主图：预分频 9 的 500 kbit/s，以及预分频 8 的 450 kbit/s。工作脚是第 45 脚和第 46 脚。由 `tools/gen_sample_figures.py` 生成 |
| `sample-14-usb-enum.svg` | 第 14 章静态主图：USBPRE=0 的 48 MHz、第 33 脚上的 1.5 kΩ，以及 USBPRE=1 的 72 MHz。由 `tools/gen_sample_figures.py` 生成 |
| `sample-15-rtos-prio.svg` | 第 15 章静态主图：1 ms 节拍上优先级 2 先于 1，以及抢占优先级 0 调用 FromISR。由 `tools/gen_sample_figures.py` 生成 |
```

拆图时追加的那一行是：

```markdown
| `sample-12-iap-vectors.svg` | 第 12 章静态局部：0x08004800 的 MSP 和 0x08004804 的复位。主图放不下 60 KB 时才拆出。由 `tools/gen_sample_figures.py` 生成 |
```

- [ ] **Step 4: 运行测试和素材检查**

Run: `python3 stm32-book/tests/test_batch5_chapters.py -v`

Expected: OK。

Run: `python3 tools/check_assets.py`

Expected: 退出码 0，输出含 `全部通过`。

- [ ] **Step 5: Commit**

```bash
git add tools/gen_sample_figures.py assets/diagrams/sample-12-iap-map.svg assets/diagrams/sample-13-can-bit.svg assets/diagrams/sample-14-usb-enum.svg assets/diagrams/sample-15-rtos-prio.svg assets/README.md stm32-book/tests/test_batch5_chapters.py
git commit -m "assets: 为 12、13、14、15 加上可印刷的静态主图"
```

若拆出了 `sample-12-iap-vectors.svg`，把它一并 `git add`。提交前再看一眼：

```bash
git diff --stat -- assets/diagrams/sample-00-boot-state.svg assets/diagrams/sample-01-swd-vectors.svg assets/diagrams/sample-02-clock-tree.svg assets/diagrams/sample-03-gpio-led.svg assets/diagrams/sample-04-exception-stack.svg assets/diagrams/sample-05-pwm-1khz.svg assets/diagrams/sample-06-uart-frame.svg assets/diagrams/sample-07-i2c-addr.svg assets/diagrams/sample-08-spi-jedec.svg assets/diagrams/sample-09-adc-sar.svg assets/diagrams/sample-10-dma-cndtr.svg assets/diagrams/sample-11-iwdg-1s.svg assets/animations/flash-iap.svg assets/animations/can-arbitration.svg assets/animations/usb-enumeration.svg assets/animations/freertos-scheduler.svg
```

Expected: 无输出。改的是 `assets/README.md` 里的说明，不是这四张旧动画 SVG。

### Task 4: Short auxiliary GIFs

**Files:**
- Modify: `tools/gen_gifs.py`（在 `BUILDERS` 之前追加四个函数，并给字典末尾加四个键。不改已有十六个函数）
- Create: `assets/gif/iap-jump.gif`
- Create: `assets/gif/can-500k.gif`
- Create: `assets/gif/usb-48m.gif`
- Create: `assets/gif/rtos-tick.gif`
- Modify: `assets/README.md`（第五节的表，以及「上面 16 张」那两句）
- Modify: `stm32-book/tests/test_batch5_chapters.py`
- Test: `stm32-book/tests/test_batch5_chapters.py`

**Interfaces:**
- Consumes: `tools/minigfx.py` 的 `Canvas`、`Gif`、`C`，以及 `chrome()`。已有的 `W` 和 `H`。
- Produces: `iap_jump()`、`can_500k()`、`usb_48m()`、`rtos_tick()`，各返回一帧数在 3 到 12 之间的 `Gif`。四个函数按这个顺序放在 `uart_idle()` 之后、`BUILDERS` 之前。`BUILDERS` 的键在原有 16 个之后增加 `"iap-jump"`、`"can-500k"`、`"usb-48m"`、`"rtos-tick"`。`iap_jump` 的源码含 `0x45670123`、`0xCDEF89AB`、`MSP`、`Reset_Handler`，不含 `0x0801FC00`，不含 `LOCK`。`can_500k` 的源码含 `250 ns`、`2 us`、`75%`、`500 kbit/s`，不含 `450`，不含 `PD0`。`usb_48m` 的源码含 `48 MHz`、`18 bytes`、`67 bytes`、`D+`，不含 `72 MHz`，不含 `1023`。`rtos_tick` 的源码含 `1 ms`、`priority 2`、`128 words`、`512 bytes`，不含 `configASSERT`，不含 `167 ns`。四条 GIF 文件都小于 500 KB。

- [ ] **Step 1: 把 GIF 断言加进测试**

在 `stm32-book/tests/test_batch5_chapters.py` 的 import 区加上 `import importlib.util`。在 `Batch5FigureTests` 之后、`if __name__` 之前追加：

```python
def _load_gifs():
    path = ROOT / "tools" / "gen_gifs.py"
    spec = importlib.util.spec_from_file_location("gen_gifs_batch5", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Batch5GifTests(unittest.TestCase):
    def test_four_auxiliary_gifs_are_short_and_ascii(self) -> None:
        gifs = _load_gifs()
        for name in (
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
        ):
            self.assertIn(name, gifs.BUILDERS)
        source = (ROOT / "tools" / "gen_gifs.py").read_text(encoding="utf-8")
        iap_src = source.split("def iap_jump", 1)[1].split("def can_500k", 1)[0]
        can_src = source.split("def can_500k", 1)[1].split("def usb_48m", 1)[0]
        usb_src = source.split("def usb_48m", 1)[1].split("def rtos_tick", 1)[0]
        rtos_src = source.split("def rtos_tick", 1)[1].split("BUILDERS", 1)[0]
        self.assertIn("0x45670123", iap_src)
        self.assertIn("0xCDEF89AB", iap_src)
        self.assertIn("MSP", iap_src)
        self.assertIn("Reset_Handler", iap_src)
        self.assertNotIn("0x0801FC00", iap_src)
        self.assertNotIn("LOCK", iap_src)
        self.assertIn("250 ns", can_src)
        self.assertIn("2 us", can_src)
        self.assertIn("75%", can_src)
        self.assertIn("500 kbit/s", can_src)
        self.assertNotIn("450", can_src)
        self.assertNotIn("PD0", can_src)
        self.assertIn("48 MHz", usb_src)
        self.assertIn("18 bytes", usb_src)
        self.assertIn("67 bytes", usb_src)
        self.assertIn("D+", usb_src)
        self.assertNotIn("72 MHz", usb_src)
        self.assertNotIn("1023", usb_src)
        self.assertIn("1 ms", rtos_src)
        self.assertIn("priority 2", rtos_src)
        self.assertIn("128 words", rtos_src)
        self.assertIn("512 bytes", rtos_src)
        self.assertNotIn("configASSERT", rtos_src)
        self.assertNotIn("167 ns", rtos_src)
        for name in ("iap-jump", "can-500k", "usb-48m", "rtos-tick"):
            gif = gifs.BUILDERS[name]()
            self.assertGreaterEqual(len(gif.frames), 3)
            self.assertLessEqual(len(gif.frames), 12)
            path = ROOT / "assets" / "gif" / f"{name}.gif"
            self.assertLess(path.stat().st_size, 500 * 1024, path.name)
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python3 stm32-book/tests/test_batch5_chapters.py Batch5GifTests -v`

Expected: FAIL，`iap-jump` 不在 `BUILDERS` 里。

- [ ] **Step 3: 追加四个 BUILDERS 并生成 GIF**

在 `tools/gen_gifs.py` 的 `uart_idle()` 之后、`BUILDERS = {` 之前插入：

```python
def iap_jump():
    """Write the two keys in order, then read MSP and Reset_Handler.

    A reversed key and the address past 64 KB stay on the static SVG.
    """
    g = Gif(W, H, delay=12)
    notes = (
        "KEY1 0x45670123",
        "KEY2 0xCDEF89AB",
        "HALF-WORD IN APP",
        "READ MSP",
        "READ Reset_Handler",
        "VTOR 0x08004800",
    )
    for index, note in enumerate(notes):
        c = Canvas(W, H)
        chrome(c, "IAP JUMP", "APP", "AUX GIF  KEY ORDER")
        c.panel(16, 48, 448, 28, C.PANEL, C.STROKE)
        c.text("0x08004800  0xB800", 28, 58, C.MUTED, 1)
        c.text(note, 28, 120, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 28, 160, C.MUTED, 1)
        c.text("MSP THEN Reset_Handler", 28, 200, C.GREEN, 1)
        c.text("PRINT THE MISS ON THE STATIC SVG", 28, 222, C.DIM, 1)
        g.add(c)
    return g


def can_500k():
    """Eight 250 ns quanta make one 2 us bit at 500 kbit/s.

    The failed prescaler row and the crystal pins stay on the static SVG.
    """
    g = Gif(W, H, delay=12)
    notes = (
        "TQ 1  250 ns",
        "TQ 2  250 ns",
        "TQ 3  250 ns",
        "TQ 6  SAMPLE 75%",
        "TQ 8  2 us",
        "500 kbit/s",
    )
    for index, note in enumerate(notes):
        c = Canvas(W, H)
        chrome(c, "CAN 500K", "36 MHz", "AUX GIF  8 QUANTA")
        c.panel(16, 48, 448, 28, C.PANEL, C.STROKE)
        c.text("prescaler 9", 28, 58, C.MUTED, 1)
        c.text(note, 28, 120, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 28, 160, C.MUTED, 1)
        c.text("75% AT 1.5 us", 28, 200, C.GREEN, 1)
        c.text("250 ns TIMES 8 IS 2 us", 28, 222, C.CYAN, 1)
        c.text("PRINT THE MISS ON THE STATIC SVG", 28, 248, C.DIM, 1)
        g.add(c)
    return g


def usb_48m():
    """D+ is pulled up, the clock is 48 MHz, then 18 and 67 bytes.

    The undivided clock and the pull-up on DM stay on the static SVG.
    """
    g = Gif(W, H, delay=12)
    notes = (
        "D+ PULL-UP",
        "HOST SEES D+",
        "USBPRE = 0",
        "48 MHz",
        "18 bytes",
        "67 bytes",
    )
    for index, note in enumerate(notes):
        c = Canvas(W, H)
        chrome(c, "USB 48M", "FS", "AUX GIF  D+")
        c.panel(16, 48, 448, 28, C.PANEL, C.STROKE)
        c.text("PA12 DP", 28, 58, C.MUTED, 1)
        c.text(note, 28, 120, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 28, 160, C.MUTED, 1)
        c.text("18 bytes THEN 67 bytes", 28, 200, C.GREEN, 1)
        c.text("48 MHz", 28, 222, C.CYAN, 1)
        c.text("PRINT THE MISS ON THE STATIC SVG", 28, 248, C.DIM, 1)
        g.add(c)
    return g


def rtos_tick():
    """A 1 ms tick keeps priority 2 on the CPU and priority 1 waiting.

    The assert stop and a SysTick clash stay on the static SVG.
    """
    g = Gif(W, H, delay=12)
    notes = (
        "TICK 1 ms",
        "TICK 1 ms",
        "priority 2 RUNS",
        "priority 1 WAITS",
        "128 words",
        "512 bytes",
    )
    for index, note in enumerate(notes):
        c = Canvas(W, H)
        chrome(c, "RTOS TICK", "1 ms", "AUX GIF  WORDS")
        c.panel(16, 48, 448, 28, C.PANEL, C.STROKE)
        c.text("1000 Hz", 28, 58, C.MUTED, 1)
        c.text(note, 28, 120, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 28, 160, C.MUTED, 1)
        c.text("priority 2 BEFORE priority 1", 28, 200, C.GREEN, 1)
        c.text("128 words = 512 bytes", 28, 222, C.CYAN, 1)
        c.text("PRINT THE ASSERT ON THE STATIC SVG", 28, 248, C.DIM, 1)
        g.add(c)
    return g
```

把 `BUILDERS` 字典在 `"iwdg-1s": iwdg_1s,` 之后加上这四行，不要改已有键的顺序：

```python
    "iap-jump": iap_jump,
    "can-500k": can_500k,
    "usb-48m": usb_48m,
    "rtos-tick": rtos_tick,
```

Run: `python3 tools/gen_gifs.py iap-jump can-500k usb-48m rtos-tick`

Expected: 退出码 0。四条 GIF 都出现，每条帧数是 6，体积远小于 500 KB。不要无参数重跑 `gen_gifs.py`，那会重写已有 16 条 GIF。

在 `assets/README.md` 第五节表格末尾、`iwdg-1s.gif` 那一行之后追加：

```markdown
| `iap-jump.gif` | 两把钥匙按顺序写完，CPU 读出 MSP 和复位。标出 0x08004800 | 由 `tools/gen_gifs.py` 生成。辅图。反序钥匙和 0x0801FC00 只在静态主图上 |
| `can-500k.gif` | 8 个 250 ns 的时间份额走过 2 µs，采样点 75%，标出 500 kbit/s | 由 `tools/gen_gifs.py` 生成。辅图。450 kbit/s 和晶振脚只在静态主图上 |
| `usb-48m.gif` | D+ 上拉被主机看见，时钟 48 MHz，随后标出 18 字节和 67 字节 | 由 `tools/gen_gifs.py` 生成。辅图。72 MHz 和接错的上拉只在静态主图上 |
| `rtos-tick.gif` | 节拍每 1 ms 走一格，优先级 2 占着 CPU，栈标成 128 words = 512 bytes | 由 `tools/gen_gifs.py` 生成。辅图。configASSERT 和 SysTick 冲突只在静态主图上 |
```

把第五节里这两句的 `16` 改成 `20`。不要改「同目录还有 20 个 `*-zh.gif`」里的 20，那是另一组文件：

```markdown
> ⚠️ 上面 16 张 GIF 的文字只能是 ASCII：`tools/minigfx.py` 内置的是 5×7 点阵英文字形。
```

```markdown
同目录还有 20 个 `*-zh.gif`。它们由 `tools/svg2gif.py` 用无头浏览器从 SVG 采样，`tools/md2mp.py` 优先拿它们做公众号插图。不是上面 16 张的中文翻译，也不由 `gen_gifs.py` 生成。
```

改成：

```markdown
> ⚠️ 上面 20 张 GIF 的文字只能是 ASCII：`tools/minigfx.py` 内置的是 5×7 点阵英文字形。
```

```markdown
同目录还有 20 个 `*-zh.gif`。它们由 `tools/svg2gif.py` 用无头浏览器从 SVG 采样，`tools/md2mp.py` 优先拿它们做公众号插图。不是上面 20 张的中文翻译，也不由 `gen_gifs.py` 生成。
```

- [ ] **Step 4: 运行测试和素材检查**

Run: `python3 stm32-book/tests/test_batch5_chapters.py -v`

Expected: OK。

Run: `python3 tools/check_assets.py`

Expected: 退出码 0，输出含 `全部通过`。

- [ ] **Step 5: Commit**

```bash
git add tools/gen_gifs.py assets/gif/iap-jump.gif assets/gif/can-500k.gif assets/gif/usb-48m.gif assets/gif/rtos-tick.gif assets/README.md stm32-book/tests/test_batch5_chapters.py
git commit -m "assets: 为 12、13、14、15 加上短 GIF 辅图"
```

提交前确认已有 16 条 GIF 没有内容 diff：

```bash
git diff --stat -- assets/gif/led-blink.gif assets/gif/pwm-breath.gif assets/gif/uart-bits.gif assets/gif/i2c-timing.gif assets/gif/dma-ring.gif assets/gif/sar-adc.gif assets/gif/nvic-preempt.gif assets/gif/uart-idle.gif assets/gif/clock-css.gif assets/gif/pwm-1khz.gif assets/gif/spi-jedec.gif assets/gif/adc-sample.gif assets/gif/swd-fetch.gif assets/gif/i2c-addr.gif assets/gif/dma-cndtr.gif assets/gif/iwdg-1s.gif
```

Expected: 无输出。

### Task 5: Thicken chapter 12 in both languages

**Files:**
- Modify: `docs/12-Flash与IAP升级.md`
- Modify: `docs/en/12-flash-iap.md`
- Modify: `stm32-book/manifest.json` 与 `stm32-book/manifest-en.json`（只追加 `rm0008-flash`，并改第 12 章罗盘。不改已有 id）
- Modify: `stm32-book/tests/test_batch5_chapters.py`
- Test: `stm32-book/tests/test_batch5_chapters.py`

**Interfaces:**
- Consumes: `iap_map()` 已写出 `assets/diagrams/sample-12-iap-map.svg`。`iap_jump()` 已写出 `assets/gif/iap-jump.gif`。Task 1 的锁定文件。Task 2 的 `rm0008-flash` 清单条目。已有 id `pm0056-vector`、`project-examples`、`ds5319-swd`、`pm0075-rdp` 只被引用，对象不改。
- Produces: 中英第 12 章各一套四块。罗盘 `sources` 成为下面测试里的 `compass`。manifest 末尾多一个 `rm0008-flash`。视频块与 `71c6723` 的字节相同。

学习目标锚点：中文 `## 📌 学习目标`，英文 `## 📌 Learning goals`。四块插在 `<!-- /video:ch12 -->` 之后、这个锚点之前。不要改锚点文字。

- [ ] **Step 1: 把章节断言加进测试**

在 `Batch5GifTests` 之后、`if __name__` 之前追加：

```python
class Batch5IapChapterTests(unittest.TestCase):
    def test_iap_chapters_have_four_blocks_and_the_same_numbers(self) -> None:
        zh_path = ROOT / "docs" / "12-Flash与IAP升级.md"
        en_path = ROOT / "docs" / "en" / "12-flash-iap.md"
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
        self.assertIn("/* F103C8 中容量 1KB/页 */", zh)
        self.assertIn("/* F103C8 medium-density, 1 KB per page */", en)
        self.assertNotIn("F103C8 小容量", zh)
        self.assertNotIn("small-capacity", en)
        zh_blocks = zh.split("## 原理与边界", 1)[1].split("## 📌 学习目标", 1)[0]
        en_blocks = en.split("## Principle and boundary", 1)[1].split("## 📌 Learning goals", 1)[0]
        for blocks in (zh_blocks, en_blocks):
            for token in (
                "0x08000000",
                "0x08004000",
                "0x08004800",
                "0x08004804",
                "0x0800FC00",
                "0x08010000",
                "0xB800",
                "0x45670123",
                "0xCDEF89AB",
                "0x0801FC00",
                "0xFFFF",
                "#source-rm0008-flash",
                "#source-pm0056-vector",
                "#source-project-examples",
                "#source-ds5319-swd",
                "#source-pm0075-rdp",
            ):
                self.assertIn(token, blocks)
            self.assertNotIn("0xAA", blocks)
            self.assertNotIn("0x1FFFF000", blocks)
            self.assertNotIn("20~40", blocks)
            self.assertNotIn("167 ns", blocks)
        self.assertIn("中容量", zh_blocks)
        self.assertIn("medium-density", en_blocks)
        self.assertIn("1 KB", zh_blocks)
        self.assertIn("1 KB", en_blocks)
        self.assertIn("../assets/diagrams/sample-12-iap-map.svg", zh)
        self.assertIn("../../assets/diagrams/sample-12-iap-map.svg", en)
        self.assertIn("../assets/gif/iap-jump.gif", zh)
        self.assertIn("../../assets/gif/iap-jump.gif", en)
        zh_key = zh.split("## 关键插图", 1)[1].split("## 时序或状态", 1)[0]
        en_key = en.split("## Key figures", 1)[1].split("## Timing or state", 1)[0]
        self.assertLess(zh_key.index("sample-12-iap-map.svg"), zh_key.index("iap-jump.gif"))
        self.assertLess(en_key.index("sample-12-iap-map.svg"), en_key.index("iap-jump.gif"))
        self.assertIn("自绘", zh_key)
        self.assertIn("Drawn for this book", en_key)
        self.assertNotIn("示意图", zh_key)
        self.assertNotIn("schematic", en_key.lower())
        self.assertIn("flash-iap.svg", zh_key)
        lock = json.loads(
            (ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch5-12-13-14-15-lock.json").read_text(
                encoding="utf-8"
            )
        )
        for path in (zh_path, en_path):
            rel = path.relative_to(ROOT).as_posix()
            baseline = subprocess.check_output(
                ["git", "-C", str(ROOT), "show", f"{lock['baseline']}:{rel}"],
            ).decode("utf-8")
            now_video = zh if path == zh_path else en
            marker = "<!-- video:ch12 -->"
            end = "<!-- /video:ch12 -->"
            self.assertEqual(
                baseline.split(marker, 1)[1].split(end, 1)[0],
                now_video.split(marker, 1)[1].split(end, 1)[0],
            )
        listed = json.loads(
            (ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch5-12-13-14-15-source-list.json").read_text(
                encoding="utf-8"
            )
        )
        by_id = {item["id"]: item for item in listed["absorb"]}
        scope_zh = (
            "第 12 章的页、半字和两把钥匙。中容量按 1 KB 擦除。编程粒度是 16 位。"
            "擦除态是 0xFFFF。解锁先写 0x45670123，再写 0xCDEF89AB。大容量的 2 KB/页在 C8 上作废。"
            "按字节编程在这颗料上作废。不重写第 02 章的等待周期。不把 0xAA 写成无保护键。"
        )
        scope_en = (
            "Chapter file 12 pages, half-words, and the two keys. Medium-density parts erase 1 KB pages. "
            "Programming granularity is 16 bits. The erased state is 0xFFFF. Unlock writes 0x45670123 and then 0xCDEF89AB. "
            "The high-density 2 KB page is void on the C8. Byte programming is void on this part. "
            "Does not rewrite the chapter 02 wait states. Does not call 0xAA the unprotected key."
        )
        zh_manifest = json.loads((ROOT / "stm32-book" / "manifest.json").read_text(encoding="utf-8"))
        en_manifest = json.loads((ROOT / "stm32-book" / "manifest-en.json").read_text(encoding="utf-8"))
        compass = [
            "rm0008",
            "an2606",
            "an3965",
            "rm0090",
            "rm0008-flash",
            "pm0056-vector",
            "project-examples",
            "ds5319-swd",
            "pm0075-rdp",
        ]
        self.assertEqual(compass, zh_manifest["chapter_guides"]["12-Flash与IAP升级.md"]["sources"])
        self.assertEqual(compass, en_manifest["chapter_guides"]["12-flash-iap.md"]["sources"])
        card_zh = zh_manifest["sources"]["rm0008-flash"]
        card_en = en_manifest["sources"]["rm0008-flash"]
        for key in ("url", "snapshot", "license"):
            self.assertEqual(by_id["rm0008-flash"][key], card_zh[key])
            self.assertEqual(card_zh[key], card_en[key])
        self.assertEqual("2026-10-25", card_zh["accessed"])
        self.assertEqual(card_zh["accessed"], card_en["accessed"])
        self.assertEqual(by_id["rm0008-flash"]["title_zh"], card_zh["title"])
        self.assertEqual(by_id["rm0008-flash"]["title_en"], card_en["title"])
        self.assertEqual(by_id["rm0008-flash"]["authority_zh"], card_zh["authority"])
        self.assertEqual(by_id["rm0008-flash"]["authority_en"], card_en["authority"])
        self.assertEqual(scope_zh, card_zh["scope"])
        self.assertEqual(scope_en, card_en["scope"])
        self.assertEqual(
            ["rm0008-flash"],
            list(zh_manifest["sources"])[-1:],
        )
```

这个测试还要用到 `json` 和 `subprocess`。若文件顶部还没有，补上：

```python
import json
import subprocess
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python3 stm32-book/tests/test_batch5_chapters.py Batch5IapChapterTests -v`

Expected: FAIL，中文稿还没有 `## 原理与边界`。

- [ ] **Step 3: 改正密度名和实验注记，并删掉旧坑表**

中文 `docs/12-Flash与IAP升级.md` 只改这三处，不要动 `<!-- video:ch12 -->` 到 `<!-- /video:ch12 -->` 之间的字节。

把

```c
#define FLASH_PAGE   1024U        /* F103C8 小容量 1KB/页 */
```

换成

```c
#define FLASH_PAGE   1024U        /* F103C8 中容量 1KB/页 */
```

把动手实验第 1 条整行换成：

```markdown
1. **读写 Flash**：把一个 32 位变量写入 `0x0800FC00`（最后一页），复位后读出验证。预期：复位后数据仍在。没有 IAP 划分、程序又没有铺到末页时，这一页可以拿来做擦写实验。地图一旦按 Bootloader 16 KB、参数区 2 KB、APP 46 KB 使用，这一页属于 APP，不是参数区外面的空页。
```

在选项字节表后面那句 `WDG_SW = 0` 的段落之前加上：

```markdown
`0xAA` 和 `0xCC` 在 STM32F103C8T6 上作废。无保护仍是 `0xA5`。解除会整片擦除主闪存。这句只留在核心原理，四块不把无保护写成 `0xAA`。
```

删掉从 `## ⚠️ 常见坑与排查` 到 `## 🧪 动手实验` 之前的整节，含表格。不要留空标题。`## 🧪 动手实验` 仍在。核心原理里已有的 YMODEM 128/1024、页擦除 `~20~40 ms`、磨损均衡和 F4 扇区表留在原地，不搬进四块。

英文 `docs/en/12-flash-iap.md` 做对应的三处。视频块同样不动。

把

```c
#define FLASH_PAGE   1024U        /* F103C8 small-capacity, 1 KB per page */
```

换成

```c
#define FLASH_PAGE   1024U        /* F103C8 medium-density, 1 KB per page */
```

把动手实验第 1 条整行换成：

```markdown
1. **Read and write Flash**: write a 32-bit variable to `0x0800FC00` (the last page) and read it back after reset. Expected: the data is still there after reset. Use that page for an erase-program experiment only when this map is not in use and the program does not already occupy the last page. Once the map is bootloader 16 KB, parameters 2 KB, and application 46 KB, that page belongs to the application.
```

在 F1/F4 选项字节表后面加上：

```markdown
`0xAA` and `0xCC` are void on STM32F103C8T6. The unprotected value remains `0xA5`. Clearing protection mass-erases main Flash. This sentence stays in the core ideas. The four sections do not call `0xAA` the unprotected value.
```

删掉从 `## ⚠️ Pitfalls and troubleshooting` 到 `## 🧪 Hands-on labs` 之前的整节。

- [ ] **Step 4: 在学习目标之前插入四块**

中文插在 `<!-- /video:ch12 -->` 与 `## 📌 学习目标` 之间。英文插在同一对标记与 `## 📌 Learning goals` 之间。视频结束标记那一行保持原样。

中文四块：

```markdown
## 原理与边界

这一章的页、半字和跳转只钉在订货号 STM32F103C8T6 上。它是中容量，闪存 64 KB，从 `0x08000000` 到 `0x08010000` 之前，1 KB 一页，共 64 页。页号从 0 到 63。第 63 页从 `0x0800FC00` 起。`0x0801FC00` 越出这 64 KB。大容量的 2 KB/页在这颗料上作废。见 [RM0008 Rev 21 第 3 章](#source-rm0008-flash)。

编程地址按 2 字节对齐，一次写 16 位。擦掉之后读回 `0xFFFF`。已经写成 0 的位，不擦整页就变不回 1。按字节编程是 F4 的句子，在 C8 上作废。一个 32 位值要分两次半字写完。

两把钥匙按这个顺序写进 `FLASH_KEYR`：先 `0x45670123`，再 `0xCDEF89AB`，`CR.LOCK` 才清除。顺序反了，锁还在，擦除返回错误。写完上锁。

这一章的地图是本书和 `examples/iap-bootloader` 已经在用的那一版，不是手册规定的唯一划分。Bootloader：`0x08000000`，16 KB，16 页，到 `0x08004000` 之前。参数区：`0x08004000`，2 KB，2 页，到 `0x08004800` 之前。APP：`0x08004800`，46 KB，46 页，长度 `0xB800`，到 `0x08010000` 之前。三块相加是 64 KB。链接脚本的起始和 `SCB->VTOR` 都是 `0x08004800`。只改其中一个，跳进去的仍是 Bootloader 的向量。

APP 区第 0 字是 MSP，第 1 字在 `0x08004804`，是 `Reset_Handler`。跳转前读出这两字，写 MSP，写 `VTOR`，再跳。`VTOR` 仍留在 0 时，中断仍进 Bootloader。这跟第 01 章同一笔，不另画启动别名。见 [PM0056](#source-pm0056-vector)。

无保护仍是 `0xA5`。解除会整片擦除主闪存。见 [PM0075](#source-pm0075-rdp)。这一章的 Bootloader 在用户闪存里。串口仍是第 06 章的第 30 脚 PA9、第 31 脚 PA10，这里只旁注。

## 关键插图

<p align="center">
  <img src="../assets/diagrams/sample-12-iap-map.svg" width="760" alt="中容量是 1 KB 页；APP 从 0x08004800 起，长度 0xB800；跳转要装入第 0 字和第 1 字">
  <br><sub>▲ 自绘。STM32F103C8T6，中容量，64 KB，1 KB 一页。正常路径先写 0x45670123，再写 0xCDEF89AB，半字写入 APP，再从 0x08004800 装入 MSP，从 0x08004804 装入复位，VTOR 写成 0x08004800。失败路径是钥匙反序、末页写成 0x0801FC00，或 VTOR 仍为 0。出处是 [RM0008 Rev 21 第 3 章](#source-rm0008-flash) 和 [PM0056](#source-pm0056-vector)。</sub>
</p>

<p align="center">
  <img src="../assets/gif/iap-jump.gif" width="640" alt="两把钥匙按顺序写完，CPU 读出 MSP 和复位">
  <br><sub>▲ 网页和公众号辅图。只播放正常路径：先 0x45670123，后 0xCDEF89AB，一个半字落进 APP，然后读出 MSP 和复位。印刷以静态主图为准。反序钥匙和 0x0801FC00 不在这条 GIF 上。</sub>
</p>

`flash-iap.svg` 留作辅图。不播放它。页边界、两把钥匙和跳转用的两字都在静态主图上。

## 时序或状态

| 区 | 起始 | 长度 | 页数 | 结束于 |
| --- | --- | --- | --- | --- |
| Bootloader | `0x08000000` | 16 KB | 16 | `0x08004000` |
| 参数区 | `0x08004000` | 2 KB | 2 | `0x08004800` |
| APP | `0x08004800` | 46 KB，`0xB800` | 46 | `0x08010000` |
| 末页 | `0x0800FC00` | 1 KB | 第 63 页 | 落在 APP 内 |
| 失败地址 | `0x0801FC00` | — | — | 不在这 64 KB 里 |
| 钥匙 | 先 `0x45670123` | 后 `0xCDEF89AB` | — | 反序清不掉 LOCK |
| 半字 | 地址 2 字节对齐 | 一次 16 位 | 擦除态 `0xFFFF` | 按字节编程在 C8 上作废 |
| 跳转 | `0x08004800` 的字是 MSP | `0x08004804` 的字是复位 | `VTOR = 0x08004800` | `VTOR` 留在 0 仍进 Bootloader |

## 坑与出处卡

| 现象 | 原因 | 处理 | 出处 | 该来源允许支持的主张 |
| --- | --- | --- | --- | --- |
| 注释写成小容量，页大小却对 | 密度名用错了 | 密度名改成中容量。页仍是 1 KB，共 64 页 | [RM0008](#source-rm0008-flash) | 中容量按 1 KB 擦除。大容量的 2 KB/页在 C8 上作废 |
| 擦除返回错误 | 钥匙顺序反了，或地址不在页边界 | 先写 KEY1，再写 KEY2。地址落在页边界上 | [RM0008](#source-rm0008-flash) | 顺序是 `0x45670123` 然后 `0xCDEF89AB`。反序清不掉 LOCK |
| 写进去的字节读回来不对 | 没按半字写，或想把 0 写回 1 | 按半字、按偶地址写。要改 0 回 1 先擦整页 | [RM0008](#source-rm0008-flash) | 编程粒度是 16 位。擦除态是 `0xFFFF`。按字节编程在这颗料上作废 |
| 跳转后死机，或中断跑回 Bootloader | 没装入两字，或 VTOR 仍为 0 | 从 `0x08004800` 装入 MSP 和复位，并写 `VTOR` | [PM0056](#source-pm0056-vector) | 第 0 字是栈初值，第 1 字是复位。这一主张不新规定对齐位数 |
| APP 长度和链接脚本对不上 | 长度没按 46 KB 写 | 起始 `0x08004800`，长度 `0xB800` | [本仓库例程](#source-project-examples) | `examples/iap-bootloader` 的 APP 是 46 KB，即 `0xB800` |
| 实验写到 `0x0801FC00` | 把 128 KB 料的末页套到了 C8 上 | C8 的最后一页是 `0x0800FC00` | [DS5319](#source-ds5319-swd) | 这条来源已经写明 STM32F103x8 的闪存是 64 KB。128 KB 的末页在这颗料上作废 |
| 按别的系列的无保护键解除读保护 | 这颗料的键不是那一个 | 无保护是 `0xA5`，解除会整片擦除 | [PM0075](#source-pm0075-rdp) | RDP 为 `0xA5` 才允许读出。编程回 `0xA5` 会先整片擦除 |
```

英文四块用同样的事实。图的路径是 `../../assets/diagrams/sample-12-iap-map.svg` 和 `../../assets/gif/iap-jump.gif`。图注里的「自绘」换成 `Drawn for this book`。替代文本用英文写出同一句结论。四块里不要出现 `0xAA`、`0x1FFFF000`、`20~40`。

```markdown
## Principle and boundary

Page size, half-word programming, and the jump are fixed on STM32F103C8T6. This part is medium-density. Flash is 64 KB, from `0x08000000` up to but not including `0x08010000`, in 1 KB pages, 64 pages. Page numbers run from 0 to 63. Page 63 starts at `0x0800FC00`. `0x0801FC00` is outside this 64 KB. A 2 KB page is the high-density sentence and is void on this part. See [RM0008 Rev 21 chapter 3](#source-rm0008-flash).

Program addresses are aligned to 2 bytes and write 16 bits. An erased half-word reads back `0xFFFF`. A bit already written to 0 does not return to 1 without erasing the page. Byte programming is an F4 sentence and is void on the C8. A 32-bit value takes two half-word writes.

The two keys are written to `FLASH_KEYR` in this order: `0x45670123`, then `0xCDEF89AB`. Only then does `CR.LOCK` clear. The reverse order leaves the lock set and the erase returns an error. Lock again when the write is done.

This map is the one already used by the book and by `examples/iap-bootloader`. It is not the only split the manual allows. Bootloader: `0x08000000`, 16 KB, 16 pages, ending before `0x08004000`. Parameters: `0x08004000`, 2 KB, 2 pages, ending before `0x08004800`. Application: `0x08004800`, 46 KB, 46 pages, length `0xB800`, ending before `0x08010000`. The three regions add up to 64 KB. The link script origin and `SCB->VTOR` are both `0x08004800`. Changing only one of them still enters the bootloader's vectors.

Word 0 of the application is the MSP. Word 1, at `0x08004804`, is `Reset_Handler`. Read both words, write the MSP, write `VTOR`, then jump. Leaving `VTOR` at 0 still delivers interrupts to the bootloader. That is the same pair of words as chapter file 01. See [PM0056](#source-pm0056-vector).

The unprotected value remains `0xA5`. Clearing it mass-erases main Flash. See [PM0075](#source-pm0075-rdp). This chapter's bootloader lives in user Flash. The UART stays on pin 30 PA9 and pin 31 PA10 from chapter file 06. That is only a side note here.

## Key figures

<p align="center">
  <img src="../../assets/diagrams/sample-12-iap-map.svg" width="760" alt="Medium-density Flash uses 1 KB pages. The application starts at 0x08004800 and is 0xB800 bytes long. The jump loads word 0 and word 1.">
  <br><sub>▲ Drawn for this book. STM32F103C8T6, medium-density, 64 KB, 1 KB pages. The normal path writes 0x45670123, then 0xCDEF89AB, programs a half-word into the application, loads the MSP from 0x08004800 and the reset word from 0x08004804, and sets VTOR to 0x08004800. The failure path is a reversed key, a last page at 0x0801FC00, or VTOR left at 0. Sources: [RM0008 Rev 21 chapter 3](#source-rm0008-flash) and [PM0056](#source-pm0056-vector).</sub>
</p>

<p align="center">
  <img src="../../assets/gif/iap-jump.gif" width="640" alt="The two keys are written in order, then the CPU reads the MSP and the reset word">
  <br><sub>▲ Auxiliary figure for the web and for posts. It plays only the normal path: 0x45670123, then 0xCDEF89AB, one half-word into the application, then the MSP and the reset word. Print from the static figure. The reversed key and 0x0801FC00 are not on this GIF.</sub>
</p>

`flash-iap.svg` stays as an auxiliary figure. Do not play it for the page boundaries, the two keys, or the two words. Those are on the static figure.

## Timing or state

| Region | Start | Length | Pages | Ends at |
| --- | --- | --- | --- | --- |
| Bootloader | `0x08000000` | 16 KB | 16 | `0x08004000` |
| Parameters | `0x08004000` | 2 KB | 2 | `0x08004800` |
| Application | `0x08004800` | 46 KB, `0xB800` | 46 | `0x08010000` |
| Last page | `0x0800FC00` | 1 KB | page 63 | inside the application |
| Failure address | `0x0801FC00` | — | — | not in this 64 KB |
| Keys | `0x45670123` first | `0xCDEF89AB` second | — | the reverse order leaves LOCK set |
| Half-word | address aligned to 2 bytes | 16 bits | erased state `0xFFFF` | byte programming is void on the C8 |
| Jump | word at `0x08004800` is the MSP | word at `0x08004804` is reset | `VTOR = 0x08004800` | `VTOR` left at 0 still enters the bootloader |

## Pitfalls and source cards

| What you see | Why | What to do | Source | Claim this source may support |
| --- | --- | --- | --- | --- |
| The comment says low density, but the page size is right | The density name is wrong | Call this part medium-density. The page stays 1 KB, 64 pages | [RM0008](#source-rm0008-flash) | Medium-density parts erase 1 KB pages. The high-density 2 KB page is void on the C8 |
| The erase returns an error | The keys are reversed, or the address is not on a page boundary | Write KEY1, then KEY2. Keep the address on a page boundary | [RM0008](#source-rm0008-flash) | The order is `0x45670123` then `0xCDEF89AB`. The reverse order does not clear LOCK |
| A written byte reads back wrong | The program was not a half-word, or a 0 was asked to become 1 | Write half-words on even addresses. Erase the page before turning a 0 back into a 1 | [RM0008](#source-rm0008-flash) | Programming granularity is 16 bits. The erased state is `0xFFFF`. Byte programming is void on this part |
| The jump dies, or interrupts return to the bootloader | The two words were not loaded, or VTOR is still 0 | Load the MSP and the reset word from `0x08004800`, and write `VTOR` | [PM0056](#source-pm0056-vector) | Word 0 is the initial stack. Word 1 is reset. This claim does not add a new alignment rule |
| The application length does not match the link script | The length is not 46 KB | Origin `0x08004800`, length `0xB800` | [examples in this repo](#source-project-examples) | `examples/iap-bootloader` sizes the application at 46 KB, which is `0xB800` |
| The experiment writes `0x0801FC00` | That is the last page of a 128 KB part | The last page on this C8 is `0x0800FC00` | [DS5319](#source-ds5319-swd) | That source already says STM32F103x8 Flash is 64 KB. The 128 KB last page is void on this part |
| Readout protection is cleared with another family's unprotected key | This part does not use that key | The unprotected value is `0xA5`. Clearing it mass-erases main Flash | [PM0075](#source-pm0075-rdp) | RDP `0xA5` allows readout. Programming `0xA5` back mass-erases first |
```

- [ ] **Step 5: 追加一个来源对象**

`url`、`snapshot`、`license` 从清单里的 `rm0008-flash` 原样复制。`title` 用 `title_zh` / `title_en`，`authority` 用 `authority_zh` / `authority_en`。`accessed` 是 `2026-10-25`。`scope` 用本任务测试里的 `scope_zh` 和 `scope_en`。中文对象追加在 `stm32-book/manifest.json` 的 `sources` 末尾，英文对象追加在 `stm32-book/manifest-en.json` 的 `sources` 末尾。不要改已有 id 的任何字段。`pm0056-vector`、`project-examples`、`ds5319-swd`、`pm0075-rdp` 只出现在罗盘里，不新建对象。

两份 manifest 里第 12 章罗盘的 `sources` 改成测试里的 `compass`。中文键是 `12-Flash与IAP升级.md`。英文键是 `12-flash-iap.md`。原来的 `rm0008`、`an2606`、`an3965`、`rm0090` 仍在，顺序不变，新 id 加在后面。

- [ ] **Step 6: 运行测试并提交**

Run: `python3 stm32-book/tests/test_batch5_chapters.py Batch5IapChapterTests -v`

Expected: OK。

```bash
git add docs/12-Flash与IAP升级.md docs/en/12-flash-iap.md stm32-book/manifest.json stm32-book/manifest-en.json stm32-book/tests/test_batch5_chapters.py
git commit -m "book: 加厚第 12 章并把密度名改成中容量"
```

不要在这一笔里改第 13、14、15 章，也不要升版本号。

### Task 6: Thicken chapter 13 in both languages

**Files:**
- Modify: `docs/13-CAN总线.md`
- Modify: `docs/en/13-can.md`
- Modify: `stm32-book/manifest.json` 与 `stm32-book/manifest-en.json`（追加 `rm0008-can`、`ds5319-usbcan`、`rm0008-usb`，并改第 13 章罗盘）
- Modify: `stm32-book/tests/test_batch5_chapters.py`
- Test: `stm32-book/tests/test_batch5_chapters.py`

**Interfaces:**
- Consumes: `can_bit()` 与 `can_500k.gif`。Task 5 已经把 `rm0008-flash` 放在 `sources` 末尾。已有 id `project-examples`、`ds5319-clock`、`ds5319-i2c` 只被引用。
- Produces: 中英第 13 章各一套四块。三个新 id 按 `rm0008-can`、`ds5319-usbcan`、`rm0008-usb` 的顺序接在 `rm0008-flash` 后面。第 14 章稍后复用 `ds5319-usbcan` 和 `rm0008-usb`，这一任务就把对象建好。视频块字节不变，所以「C8 没有那两只脚」仍只出现在视频块里。

学习目标锚点：中文 `## 📌 学习目标`。英文是 `## 📌 Goals`，不是 `Learning goals`。核心原理的英文标题保持 `## 🧠 Core idea`。旧坑标题英文是 `## ⚠️ Pitfalls`。不要把这些标题改长。

- [ ] **Step 1: 把章节断言加进测试**

在 `Batch5IapChapterTests` 之后追加 `Batch5CanChapterTests`。需要文件顶部已有 `json` 和 `subprocess`。

```python
class Batch5CanChapterTests(unittest.TestCase):
    def test_can_chapters_have_four_blocks_and_the_same_numbers(self) -> None:
        zh_path = ROOT / "docs" / "13-CAN总线.md"
        en_path = ROOT / "docs" / "en" / "13-can.md"
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
        self.assertNotIn("## ⚠️ Pitfalls\n", en)
        self.assertIn("## 📌 学习目标", zh)
        self.assertIn("## 📌 Goals", en)
        self.assertIn("## 🧠 核心原理", zh)
        self.assertIn("## 🧠 Core idea", en)
        self.assertNotIn("## 📌 Learning goals", en)
        zh_video, zh_rest = _split_video(zh, "ch13")
        en_video, en_rest = _split_video(en, "ch13")
        self.assertIn("C8 没有那两只脚", zh_video)
        self.assertIn("C8 没有那两只脚", en_video)
        self.assertNotIn("C8 没有那两只脚", zh_rest)
        self.assertNotIn("C8 没有那两只脚", en_rest)
        self.assertNotIn("差分阻抗约 60", zh_rest)
        self.assertNotIn("differential impedance near 60", en_rest)
        self.assertIn("PB8=CAN_RX、PB9=CAN_TX", zh_rest)
        self.assertIn("PB8 = CAN_RX, PB9 = CAN_TX", en_rest)
        zh_blocks = zh.split("## 原理与边界", 1)[1].split("## 📌 学习目标", 1)[0]
        en_blocks = en.split("## Principle and boundary", 1)[1].split("## 📌 Goals", 1)[0]
        for blocks in (zh_blocks, en_blocks):
            for token in (
                "36",
                "250",
                "500",
                "450",
                "75",
                "70",
                "256",
                "128",
                "11",
                "120",
                "PB8",
                "PB9",
                "PA11",
                "PA12",
                "PD0",
                "PD1",
                "#source-rm0008-can",
                "#source-project-examples",
                "#source-ds5319-usbcan",
                "#source-ds5319-clock",
                "#source-ds5319-i2c",
                "#source-rm0008-usb",
            ):
                self.assertIn(token, blocks)
        self.assertIn("第 45 脚", zh_blocks)
        self.assertIn("第 46 脚", zh_blocks)
        self.assertIn("第 5 脚", zh_blocks)
        self.assertIn("第 6 脚", zh_blocks)
        self.assertIn("pin 45", en_blocks)
        self.assertIn("pin 46", en_blocks)
        self.assertIn("pin 5", en_blocks)
        self.assertIn("pin 6", en_blocks)
        self.assertIn("不是电缆", zh_blocks)
        self.assertIn("not the cable", en_blocks)
        self.assertIn("../assets/diagrams/sample-13-can-bit.svg", zh)
        self.assertIn("../../assets/diagrams/sample-13-can-bit.svg", en)
        self.assertIn("../assets/gif/can-500k.gif", zh)
        self.assertIn("../../assets/gif/can-500k.gif", en)
        zh_key = zh.split("## 关键插图", 1)[1].split("## 时序或状态", 1)[0]
        en_key = en.split("## Key figures", 1)[1].split("## Timing or state", 1)[0]
        self.assertLess(zh_key.index("sample-13-can-bit.svg"), zh_key.index("can-500k.gif"))
        self.assertLess(en_key.index("sample-13-can-bit.svg"), en_key.index("can-500k.gif"))
        self.assertIn("自绘", zh_key)
        self.assertIn("Drawn for this book", en_key)
        self.assertNotIn("示意图", zh_key)
        lock = json.loads(
            (ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch5-12-13-14-15-lock.json").read_text(
                encoding="utf-8"
            )
        )
        for path, now in ((zh_path, zh), (en_path, en)):
            rel = path.relative_to(ROOT).as_posix()
            baseline = subprocess.check_output(
                ["git", "-C", str(ROOT), "show", f"{lock['baseline']}:{rel}"],
            ).decode("utf-8")
            marker = "<!-- video:ch13 -->"
            end = "<!-- /video:ch13 -->"
            self.assertEqual(
                baseline.split(marker, 1)[1].split(end, 1)[0],
                now.split(marker, 1)[1].split(end, 1)[0],
            )
        zh_manifest = json.loads((ROOT / "stm32-book" / "manifest.json").read_text(encoding="utf-8"))
        en_manifest = json.loads((ROOT / "stm32-book" / "manifest-en.json").read_text(encoding="utf-8"))
        compass = [
            "rm0008",
            "rm0008-can",
            "ds5319-usbcan",
            "rm0008-usb",
            "project-examples",
            "ds5319-clock",
            "ds5319-i2c",
        ]
        self.assertEqual(compass, zh_manifest["chapter_guides"]["13-CAN总线.md"]["sources"])
        self.assertEqual(compass, en_manifest["chapter_guides"]["13-can.md"]["sources"])
        self.assertEqual(
            ["rm0008-flash", "rm0008-can", "ds5319-usbcan", "rm0008-usb"],
            list(zh_manifest["sources"])[-4:],
        )


def _split_video(text: str, slug: str) -> tuple[str, str]:
    marker = f"<!-- video:{slug} -->"
    end = f"<!-- /video:{slug} -->"
    video = text.split(marker, 1)[1].split(end, 1)[0]
    rest = text.split(marker, 1)[0] + text.split(end, 1)[1]
    return video, rest
```

`self.assertNotIn("## ⚠️ Pitfalls\n", en)` 会在四块标题不存在时先因别的断言失败。四块写完之后，英文旧标题必须已经删掉。若正文别处还有单独一行 `## ⚠️ Pitfalls`，删的就是旧坑那一节，不要去改别的二级标题。

- [ ] **Step 2: 运行测试，确认失败**

Run: `python3 stm32-book/tests/test_batch5_chapters.py Batch5CanChapterTests -v`

Expected: FAIL，中文稿还没有 `## 原理与边界`。

- [ ] **Step 3: 改正终端电阻和 BluePill 脚，并删掉旧坑表**

中文只改视频块以外的这两处，然后删掉旧坑节。

把

```markdown
- 总线两端各接一个 **120 Ω 终端电阻**，消除反射、保证差分阻抗约 60 Ω。
```

换成

```markdown
- 总线两端各接一只 **120 Ω**，接在 CANH 与 CANL 之间，不接在 MCU 脚上。两只 120 Ω 并联，直流负载是 60 Ω。60 Ω 不是电缆的特性阻抗。
```

把硬件表的 BluePill CAN1 行

```markdown
| BluePill (F103) | CAN1 | PA11=CAN_RX、PA12=CAN_TX | 外接 TJA1050/SN65HVD230 收发器 |
```

换成

```markdown
| BluePill (F103) | CAN1 | PB8=CAN_RX、PB9=CAN_TX | 第一种重映射。第 45 脚收，第 46 脚发。PA11/PA12 是复位默认，和 USB 冲突，不走这条正常路径。外接 TJA1050/SN65HVD230 |
```

收发器供电那句「SN65HVD230 是 3.3 V，TJA1050 是 5 V」留在硬件节。1 Mbps 那一行留在核心原理的波特率表里。在那张表后面已有的 70% 注记末尾加上这一句，不要把 1 Mbps 搬进四块：

```markdown
1 Mbps 那一行的采样点是 66.7%。「采样点一般在 75% 到 87.5%」不覆盖这一行。四块的工作点只取 500 kbit/s。
```

删掉从 `## ⚠️ 常见坑与排查` 到 `## 🧪 动手实验` 之前的整节。

英文做对应替换。

把

```markdown
- Put a **120 Ω** terminator at each end of the bus. That kills reflections and sets the differential impedance near 60 Ω.
```

换成

```markdown
- Put one **120 Ω** resistor at each end of the bus, between CANH and CANL, not on the MCU pins. Two 120 Ω resistors in parallel are a 60 Ω DC load. 60 Ω is not the cable impedance.
```

把

```markdown
| BluePill (F103) | CAN1 | PA11 = CAN_RX, PA12 = CAN_TX | External TJA1050 / SN65HVD230 |
```

换成

```markdown
| BluePill (F103) | CAN1 | PB8 = CAN_RX, PB9 = CAN_TX | First remap. Pin 45 receives and pin 46 transmits. PA11/PA12 are the reset default and conflict with USB, so they are not this normal path. External TJA1050 / SN65HVD230 |
```

在英文波特率表的 70% 注记末尾加上：

```markdown
The 1 Mbps row samples at 66.7%. The sentence "sample around 75% to 87.5%" does not cover that row. The four sections use only the 500 kbit/s working point.
```

删掉从 `## ⚠️ Pitfalls` 到 `## 🧪 Try it` 之前的整节。不要把 `## 📌 Goals` 改成 `## 📌 Learning goals`。

Nucleo-F411RE 那一行写的是另一块板的 PD0/PD1，留在硬件表。不要把它改写成「C8 没有这两只脚」。

- [ ] **Step 4: 在学习目标之前插入四块**

中文锚点是 `## 📌 学习目标`。英文锚点是 `## 📌 Goals`。

中文四块：

```markdown
## 原理与边界

这一章的位时间和工作脚只钉在订货号 STM32F103C8T6 上。CAN1 的内核时钟是 APB1 的 36 MHz，跟第 02 章同一笔。工作点整格照抄罗盘：预分频 9，BS1 = 5，BS2 = 2，SJW = 1。见 [RM0008 Rev 21 bxCAN](#source-rm0008-can)。

时间份额 `Tq = 9 / 36e6 = 250` ns。同步段 1，加 BS1 的 5，加 BS2 的 2，一共 8。位时间 `8 × 250 ns = 2` µs，也就是 500 kbit/s。采样点 `(1 + 5) / 8 = 75%`，落在 1.5 µs。这是正常路径。

想要 10 个时间份额、采样点 70%（BS1 = 6，BS2 = 3）时，预分频是 7.2，不是整数。写成 8 时，`36e6 / (8 × 10) = 450` kbit/s。这是失败路径。1 Mbit/s 留在核心原理，不作为这一节的工作点。

BluePill 上用第一种重映射：第 45 脚 PB8 = CAN_RX，第 46 脚 PB9 = CAN_TX。复位默认是第 32 脚 PA11 = CAN_RX，第 33 脚 PA12 = CAN_TX。那一对是第 14 章 USB 的正常路径。见 [DS5319 Rev 20 表 5](#source-ds5319-usbcan)。

第 5 脚 PD0、第 6 脚 PD1 在 LQFP48 上有，它们是 HSE。重映射到这两只脚会停掉 8 MHz 晶振。见 [DS5319](#source-ds5319-clock)。第 45 脚和第 46 脚也是第 07 章的 I2C1 重映射。这一张主图不把 CAN 和 I2C 画成同时有效。见 [DS5319](#source-ds5319-i2c)。

总线两端各一只 120 Ω，接在 CANH 与 CANL 之间。MCU 的 PB8/PB9 进收发器的 RXD/TXD，收发器才出 CANH/CANL。两只 120 Ω 并联，直流负载是 60 Ω。60 Ω 不是电缆的特性阻抗。

只有一个节点、又不是回环时，没有应答，发送错误计数涨到 256，节点停止驱动总线。恢复是 128 次、每次 11 个连续隐性位。32 位掩码里，标准 ID 写入 `FilterIdHigh` 时左移 5 位。不左移时，总线上有帧，邮箱仍是空的。14 组过滤器和 2 个 FIFO 留在边界。见 [本仓库例程](#source-project-examples)。

`USB_LP_CAN1_RX0` 与第 14 章是同一条向量。两个例程不要编进同一个工程。见 [RM0008](#source-rm0008-usb)。

## 关键插图

<p align="center">
  <img src="../assets/diagrams/sample-13-can-bit.svg" width="760" alt="36 MHz 下预分频 9、8 个时间份额是 500 kbit/s；写成预分频 8 和 10 个时间份额是 450 kbit/s；工作脚是第 45 脚和第 46 脚">
  <br><sub>▲ 自绘。STM32F103C8T6。正常路径是 8 个 250 ns 的时间份额，采样点 75%，2 µs，500 kbit/s，预分频 9，SJW = 1。120 Ω 接在 CANH 与 CANL 上。失败路径是预分频 8、10 个时间份额、450 kbit/s、采样点 70%。工作脚是第 45 脚 PB8 和第 46 脚 PB9。出处是 [RM0008 Rev 21 bxCAN](#source-rm0008-can) 和 [DS5319 Rev 20 表 5](#source-ds5319-usbcan)。</sub>
</p>

<p align="center">
  <img src="../assets/gif/can-500k.gif" width="640" alt="8 个时间份额走过 2 µs，采样点在 75%">
  <br><sub>▲ 网页和公众号辅图。只播放正常路径：8 个 250 ns 的时间份额，采样点 75%，500 kbit/s。印刷以静态主图为准。450 kbit/s 和晶振脚不在这条 GIF 上。</sub>
</p>

`can-arbitration.svg` 留作辅图。仲裁和位填充不进这张静态主图。

## 时序或状态

| 预分频 | BS1 | BS2 | 时间份额数 | 位时间 | 速率 | 采样点 |
| --- | --- | --- | --- | --- | --- | --- |
| 9 | 5 | 2 | 8 | 2 µs | 500 kbit/s | 75%。时间份额 250 ns。正常 |
| 8 | 6 | 3 | 10 | 不是 2 µs | 450 kbit/s | 70%。失败 |
| 脚位 | PB8 收 | PB9 发 | 第 45 脚、第 46 脚 | — | — | PA11/PA12 与 USB 冲突 |
| 错误 | 计数到 256 | 总线关闭 | 128 次 | 每次 11 个隐性位 | — | 之后才可以再驱动 |
| 过滤器 | `FilterIdHigh` | 左移 5 | — | — | — | 不左移则邮箱仍空 |

## 坑与出处卡

| 现象 | 原因 | 处理 | 出处 | 该来源允许支持的主张 |
| --- | --- | --- | --- | --- |
| 示波器或分析仪上是 450 kbit/s | 预分频和段数配成了除不尽的那一档 | 预分频用 9，BS1 用 5，BS2 用 2 | [RM0008](#source-rm0008-can) | 8 个时间份额、预分频 9，在 36 MHz 下是 500 kbit/s。10 个时间份额配预分频 8 是 450 kbit/s |
| 单节点、正常模式，发几帧就闭嘴 | 没有应答，发送错误计数涨满 | 先用回环。上总线时要有应答节点 | [RM0008](#source-rm0008-can) | 发送错误计数到 256 进入总线关闭。恢复要 128 次、每次 11 个隐性位 |
| 总线上有帧，邮箱是空的 | 标准 ID 没有左移 | 写入 `FilterIdHigh` 时左移 5 | [本仓库例程](#source-project-examples) | `examples/can-bxcan` 用 `PEER_ID << 5` 填 `FilterIdHigh`。预分频宏是 9 |
| 两端都在报错 | 位时间不一致，或终端没接在总线两端 | 两端同一组位时间，CANH 与 CANL 之间两端各 120 Ω | [本仓库例程](#source-project-examples) | 例程要求两端各一只 120 Ω。这一行不规定电缆特性阻抗，也不规定收发器是 5 V 还是 3.3 V |
| 波形在 PA11/PA12，USB 也失效 | 还停在复位默认脚上 | 重映射到第 45 脚和第 46 脚 | [DS5319](#source-ds5319-usbcan) | 复位默认 CAN 在 PA11/PA12。PB8/PB9 是重映射。PA11/PA12 同时是 USB |
| 重映射到晶振脚之后时钟停了 | 那两只脚接着 HSE | 不要把 CAN 放到第 5 脚和第 6 脚 | [DS5319](#source-ds5319-clock) | LQFP48 第 5 脚是 PD0-OSC_IN，第 6 脚是 PD1-OSC_OUT。这两只脚存在 |
| 和 I2C 重映射抢同一对脚 | PB8/PB9 也是 I2C1 的重映射 | 这一对脚只选择 CAN 或 I2C 之一 | [DS5319](#source-ds5319-i2c) | 第 45 脚 PB8、第 46 脚 PB9 是 I2C1 的重映射。不改写第 07 章那张图 |
```

英文四块路径用 `../../assets/...`。图注写 `Drawn for this book`。保留上面每一个数字。四块要写明 PD0/PD1 在封装上存在，并写明 60 Ω 不是电缆特性阻抗。英文用 `not the cable`。不要写 `characteristic impedance`。

```markdown
## Principle and boundary

Bit time and the working pins are fixed on STM32F103C8T6. The CAN1 kernel clock is the 36 MHz APB1 clock, the same account as chapter file 02. The working point is copied from the compass: prescaler 9, BS1 = 5, BS2 = 2, SJW = 1. See [RM0008 Rev 21 bxCAN](#source-rm0008-can).

One time quantum is `Tq = 9 / 36e6 = 250` ns. One synchronization quantum, plus BS1 of 5, plus BS2 of 2, is 8. The bit lasts `8 × 250 ns = 2` µs, which is 500 kbit/s. The sample point is `(1 + 5) / 8 = 75%`, at 1.5 µs. That is the normal path.

Ten quanta at a 70% sample point (BS1 = 6, BS2 = 3) wants a prescaler of 7.2, which is not an integer. Writing 8 gives `36e6 / (8 × 10) = 450` kbit/s. That is the failure path. The 1 Mbit/s row stays in the core ideas and is not this section's working point.

On a BluePill the first remap is the working pair: pin 45 PB8 = CAN_RX, pin 46 PB9 = CAN_TX. The reset default is pin 32 PA11 = CAN_RX and pin 33 PA12 = CAN_TX. That pair is the normal path of the USB chapter. See [DS5319 Rev 20 Table 5](#source-ds5319-usbcan).

Pin 5 PD0 and pin 6 PD1 exist on LQFP48. They are the HSE pins. Remapping CAN onto them stops the 8 MHz crystal. See [DS5319](#source-ds5319-clock). Pin 45 and pin 46 are also the I2C1 remap from chapter file 07. This figure does not draw CAN and I2C active together. See [DS5319](#source-ds5319-i2c).

Each end of the bus has one 120 Ω resistor between CANH and CANL. PB8 and PB9 enter the transceiver RXD and TXD. Only the transceiver drives CANH and CANL. Two 120 Ω resistors in parallel are a 60 Ω DC load. 60 Ω is not the cable impedance.

A single node that is not in loopback gets no acknowledge. The transmit error counter reaches 256 and the node stops driving the bus. Recovery is 128 times 11 consecutive recessive bits. In a 32-bit mask, a standard ID written to `FilterIdHigh` is shifted left by 5. Without that shift the bus can carry frames while the mailbox stays empty. Fourteen filter banks and two FIFOs stay in the boundary. See [examples in this repo](#source-project-examples).

`USB_LP_CAN1_RX0` is the same vector as chapter file 14. Do not link the two examples into one project. See [RM0008](#source-rm0008-usb).

## Key figures

<p align="center">
  <img src="../../assets/diagrams/sample-13-can-bit.svg" width="760" alt="At 36 MHz, prescaler 9 and eight quanta is 500 kbit/s. Prescaler 8 and ten quanta is 450 kbit/s. The working pins are pin 45 and pin 46.">
  <br><sub>▲ Drawn for this book. STM32F103C8T6. The normal path is eight 250 ns quanta, a 75% sample point, 2 µs, 500 kbit/s, prescaler 9, SJW = 1. The 120 Ω resistors sit on CANH and CANL. The failure path is prescaler 8, ten quanta, 450 kbit/s, and a 70% sample point. The working pins are pin 45 PB8 and pin 46 PB9. Sources: [RM0008 Rev 21 bxCAN](#source-rm0008-can) and [DS5319 Rev 20 Table 5](#source-ds5319-usbcan).</sub>
</p>

<p align="center">
  <img src="../../assets/gif/can-500k.gif" width="640" alt="Eight quanta cross 2 µs and the sample point is at 75%">
  <br><sub>▲ Auxiliary figure for the web and for posts. It plays only the normal path: eight 250 ns quanta, a 75% sample point, and 500 kbit/s. Print from the static figure. 450 kbit/s and the crystal pins are not on this GIF.</sub>
</p>

`can-arbitration.svg` stays as an auxiliary figure. Arbitration and bit stuffing are not on this static figure.

## Timing or state

| Prescaler | BS1 | BS2 | Quanta | Bit time | Rate | Sample point |
| --- | --- | --- | --- | --- | --- | --- |
| 9 | 5 | 2 | 8 | 2 µs | 500 kbit/s | 75%. Quantum 250 ns. Normal |
| 8 | 6 | 3 | 10 | not 2 µs | 450 kbit/s | 70%. Failure |
| Pins | PB8 receives | PB9 transmits | pin 45 and pin 46 | — | — | PA11/PA12 conflict with USB |
| Errors | count reaches 256 | bus-off | 128 times | 11 recessive bits each time | — | only then may the node drive again |
| Filter | `FilterIdHigh` | shift left by 5 | — | — | — | without the shift the mailbox stays empty |

## Pitfalls and source cards

| What you see | Why | What to do | Source | Claim this source may support |
| --- | --- | --- | --- | --- |
| The scope or analyzer shows 450 kbit/s | The prescaler and the segment counts used the row that does not divide | Use prescaler 9, BS1 5, and BS2 2 | [RM0008](#source-rm0008-can) | Eight quanta and prescaler 9 is 500 kbit/s at 36 MHz. Ten quanta with prescaler 8 is 450 kbit/s |
| One node in normal mode goes silent after a few frames | There is no acknowledge, so the transmit error counter fills | Start in loopback. On a real bus, provide a node that acknowledges | [RM0008](#source-rm0008-can) | A transmit error counter of 256 enters bus-off. Recovery takes 128 times 11 recessive bits |
| Frames are on the bus and the mailbox is empty | The standard ID was not shifted | Shift left by 5 when writing `FilterIdHigh` | [examples in this repo](#source-project-examples) | `examples/can-bxcan` fills `FilterIdHigh` with `PEER_ID << 5`. The prescaler macro is 9 |
| Both ends report errors | The bit timing differs, or the terminators are not at the two ends | Use one bit timing, and put 120 Ω between CANH and CANL at each end | [examples in this repo](#source-project-examples) | The example asks for one 120 Ω resistor at each end. This row does not set a cable impedance and does not set the transceiver supply at 5 V or 3.3 V |
| The waveform is on PA11/PA12 and USB also fails | The pins are still the reset default | Remap to pin 45 and pin 46 | [DS5319](#source-ds5319-usbcan) | Reset-default CAN is on PA11/PA12. PB8/PB9 is the remap. PA11/PA12 are also USB |
| The clock stops after a remap onto the crystal pins | Those pins carry HSE | Do not put CAN on pin 5 and pin 6 | [DS5319](#source-ds5319-clock) | LQFP48 pin 5 is PD0-OSC_IN and pin 6 is PD1-OSC_OUT. Both pins exist |
| I2C remap wants the same pair | PB8/PB9 is also the I2C1 remap | Choose either CAN or I2C on that pair | [DS5319](#source-ds5319-i2c) | Pin 45 PB8 and pin 46 PB9 are the I2C1 remap. Do not redraw the chapter 07 figure |
```

英文四块里写 `60 Ω is not the cable impedance.` 不要写 `characteristic impedance`。测试要能在四块里找到 `not the cable`。

- [ ] **Step 5: 追加三个来源对象**

按 `rm0008-can`、`ds5319-usbcan`、`rm0008-usb` 的顺序追加到两份 manifest 的 `sources` 末尾，接在 `rm0008-flash` 后面。`url`、`snapshot`、`license` 从清单原样复制。`accessed` 是 `2026-10-25`。`title` 和 `authority` 用清单里的中英字段。

三个 `scope` 用下面这三对，中英各一句，整段复制，不要改字：

`rm0008-can` 中文：`第 13 章的位时间、总线关闭和过滤器。36 MHz 下预分频 9、8 个时间份额是 500 kbit/s。预分频 8、10 个时间份额是 450 kbit/s。发送错误计数到 256 进入总线关闭。恢复是 128 次、每次 11 个隐性位。不编 CAN 基址。不把 450 kbit/s 写成工作点。`

`rm0008-can` 英文：`Chapter file 13 bit time, bus-off, and filters. At 36 MHz, prescaler 9 and eight quanta is 500 kbit/s. Prescaler 8 and ten quanta is 450 kbit/s. A transmit error counter of 256 enters bus-off. Recovery is 128 times 11 recessive bits. Does not invent a CAN base address. Does not call 450 kbit/s the working point.`

`ds5319-usbcan` 中文：`第 13 章和第 14 章的脚。第 32 脚 PA11 的复用含 USB_DM 和 CAN_RX，第 33 脚 PA12 的复用含 USB_DP 和 CAN_TX。第 45 脚 PB8、第 46 脚 PB9 是 CAN 重映射。第 5 脚和第 6 脚存在。同一对 PA11/PA12 不能同时当 CAN 和 USB。`

`ds5319-usbcan` 英文：`Pins for chapter files 13 and 14. Pin 32 PA11 includes USB_DM and CAN_RX. Pin 33 PA12 includes USB_DP and CAN_TX. Pin 45 PB8 and pin 46 PB9 are the CAN remap. Pin 5 and pin 6 exist. PA11/PA12 cannot be CAN and USB at the same time.`

`rm0008-usb` 中文：`第 14 章的设备边界，以及第 13 章对同一条中断的交叉引用。F103 的 USB 是全速设备，不是主机。USB 时钟要 48 MHz。默认向量名是 USB_LP_CAN1_RX0。不把 480 Mbit/s 写进这颗料。`

`rm0008-usb` 英文：`The device boundary for chapter file 14, and the chapter file 13 cross-reference to the same interrupt. F103 USB is a full-speed device, not a host. The USB clock must be 48 MHz. The default vector name is USB_LP_CAN1_RX0. Does not write 480 Mbit/s onto this part.`

第 13 章罗盘改成测试里的 `compass`。不删除原来的 `rm0008`。`project-examples`、`ds5319-clock`、`ds5319-i2c` 不新建对象。

在 `Batch5CanChapterTests` 里为这三个 id 补上和 Task 5 相同形状的字段断言：`url`、`snapshot`、`license` 与清单相同，中英相同，`accessed` 是 `2026-10-25`，`title`、`authority`、`scope` 用上面的字符串。断言失败就改 manifest，不要改短 scope。

- [ ] **Step 6: 运行测试并提交**

Run: `python3 stm32-book/tests/test_batch5_chapters.py Batch5CanChapterTests -v`

Expected: OK。

```bash
git add docs/13-CAN总线.md docs/en/13-can.md stm32-book/manifest.json stm32-book/manifest-en.json stm32-book/tests/test_batch5_chapters.py
git commit -m "book: 加厚第 13 章并把 500 kbit/s 钉在 PB8/PB9"
```

`git diff --stat -- assets/animations/can-arbitration.svg` 应无输出。视频块的 diff 应为空。

### Task 7: Thicken chapter 14 in both languages

**Files:**
- Modify: `docs/14-USB.md`
- Modify: `docs/en/14-usb.md`
- Modify: `stm32-book/manifest.json` 与 `stm32-book/manifest-en.json`（只改第 14 章罗盘。不新建 id。`ds5319-usbcan` 和 `rm0008-usb` 已在 Task 6 落盘。`rm0008-rcc` 是已有 id）
- Modify: `stm32-book/tests/test_batch5_chapters.py`
- Test: `stm32-book/tests/test_batch5_chapters.py`

**Interfaces:**
- Consumes: `usb_enum()` 与 `usb-48m.gif`。Task 6 的 `ds5319-usbcan`、`rm0008-usb`。已有 `rm0008-rcc` 和 `project-examples`。
- Produces: 中英第 14 章各一套四块。罗盘在原有 `rm0008`、`usb20`、`project-examples` 之后追加 `rm0008-rcc`、`ds5319-usbcan`、`rm0008-usb`。不产生新的 source id。视频块字节不变。10 ms 仍只留在核心原理的枚举表里。

英文锚点是 `## 📌 Goals`。英文核心标题保持 `## 🧠 Core idea`。英文旧坑标题是 `## ⚠️ Pitfalls`。

- [ ] **Step 1: 把章节断言加进测试**

在 `Batch5CanChapterTests` 之后追加：

```python
class Batch5UsbChapterTests(unittest.TestCase):
    def test_usb_chapters_have_four_blocks_and_the_same_numbers(self) -> None:
        zh_path = ROOT / "docs" / "14-USB.md"
        en_path = ROOT / "docs" / "en" / "14-usb.md"
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
        self.assertNotIn("## ⚠️ Pitfalls\n", en)
        self.assertIn("## 📌 Goals", en)
        self.assertIn("## 🧠 Core idea", en)
        self.assertIn("0x1209/0x0001", zh)
        self.assertIn("0x1209/0x0001", en)
        zh_blocks = zh.split("## 原理与边界", 1)[1].split("## 📌 学习目标", 1)[0]
        en_blocks = en.split("## Principle and boundary", 1)[1].split("## 📌 Goals", 1)[0]
        for blocks in (zh_blocks, en_blocks):
            for token in (
                "USBPRE",
                "48",
                "72",
                "18",
                "67",
                "0x0043",
                "0x1209",
                "0x0001",
                "64",
                "0x32",
                "100",
                "1023",
                "1.5",
                "#source-rm0008-rcc",
                "#source-ds5319-usbcan",
                "#source-project-examples",
                "#source-rm0008-usb",
            ):
                self.assertIn(token, blocks)
            self.assertNotIn("10 ms", blocks)
            self.assertNotIn("90 Ω", blocks)
            self.assertNotIn("90 ohm", blocks.lower())
        self.assertIn("是设备", zh_blocks)
        self.assertIn("not a host", en_blocks)
        self.assertIn("不是这份", zh_blocks)
        self.assertIn("not this descriptor", en_blocks)
        self.assertIn("第 32 脚", zh_blocks)
        self.assertIn("第 33 脚", zh_blocks)
        self.assertIn("pin 32", en_blocks)
        self.assertIn("pin 33", en_blocks)
        self.assertIn("../assets/diagrams/sample-14-usb-enum.svg", zh)
        self.assertIn("../../assets/diagrams/sample-14-usb-enum.svg", en)
        self.assertIn("../assets/gif/usb-48m.gif", zh)
        self.assertIn("../../assets/gif/usb-48m.gif", en)
        zh_key = zh.split("## 关键插图", 1)[1].split("## 时序或状态", 1)[0]
        en_key = en.split("## Key figures", 1)[1].split("## Timing or state", 1)[0]
        self.assertLess(zh_key.index("sample-14-usb-enum.svg"), zh_key.index("usb-48m.gif"))
        self.assertLess(en_key.index("sample-14-usb-enum.svg"), en_key.index("usb-48m.gif"))
        self.assertIn("自绘", zh_key)
        self.assertIn("Drawn for this book", en_key)
        self.assertNotIn("示意图", zh_key)
        lock = json.loads(
            (ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch5-12-13-14-15-lock.json").read_text(
                encoding="utf-8"
            )
        )
        for path, now in ((zh_path, zh), (en_path, en)):
            rel = path.relative_to(ROOT).as_posix()
            baseline = subprocess.check_output(
                ["git", "-C", str(ROOT), "show", f"{lock['baseline']}:{rel}"],
            ).decode("utf-8")
            marker = "<!-- video:ch14 -->"
            end = "<!-- /video:ch14 -->"
            self.assertEqual(
                baseline.split(marker, 1)[1].split(end, 1)[0],
                now.split(marker, 1)[1].split(end, 1)[0],
            )
        zh_manifest = json.loads((ROOT / "stm32-book" / "manifest.json").read_text(encoding="utf-8"))
        en_manifest = json.loads((ROOT / "stm32-book" / "manifest-en.json").read_text(encoding="utf-8"))
        compass = [
            "rm0008",
            "usb20",
            "project-examples",
            "rm0008-rcc",
            "ds5319-usbcan",
            "rm0008-usb",
        ]
        self.assertEqual(compass, zh_manifest["chapter_guides"]["14-USB.md"]["sources"])
        self.assertEqual(compass, en_manifest["chapter_guides"]["14-usb.md"]["sources"])
        self.assertNotIn("rm0008-rcc-pullup", zh_manifest["sources"])
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python3 stm32-book/tests/test_batch5_chapters.py Batch5UsbChapterTests -v`

Expected: FAIL，中文稿还没有 `## 原理与边界`。

- [ ] **Step 3: 标明本仓库的 VID，并删掉旧坑表**

中文描述符表这一行：

```markdown
| 设备 | `idVendor`/`idProduct` | VID/PID，ST 官方例程常用 0x0483/0x5740 |
```

换成：

```markdown
| 设备 | `idVendor`/`idProduct` | ST 官方例程常用 0x0483/0x5740。本仓库 examples/usb-cdc 不是这一对，用 0x1209/0x0001 |
```

英文这一行：

```markdown
| Device | `idVendor` / `idProduct` | VID/PID. ST's own examples often use 0x0483/0x5740 |
```

换成：

```markdown
| Device | `idVendor` / `idProduct` | ST examples often use 0x0483/0x5740. This repository's examples/usb-cdc does not. It uses 0x1209/0x0001 |
```

枚举表里「D+/D- 同时拉低 ≥ 10 ms」留在核心原理。不要把它搬进四块。

删掉中文从 `## ⚠️ 常见坑与排查` 到 `## 🧪 动手实验` 之前的整节。删掉英文从 `## ⚠️ Pitfalls` 到 `## 🧪 Try it` 之前的整节。不要把 `## 📌 Goals` 改名。

- [ ] **Step 4: 在学习目标之前插入四块**

中文：

```markdown
## 原理与边界

这一章的时钟和描述符只钉在订货号 STM32F103C8T6 上。USB 时钟整格照抄第 02 章和罗盘。PLL 是 72 MHz。`USBPRE = 0` 再除以 1.5，USB 时钟是 48 MHz。`USBPRE = 1` 不除，USB 时钟是 72 MHz，主机在读描述符时失败。见 [RM0008](#source-rm0008-rcc)。不重画时钟树。

第 32 脚 PA11 = USB_DM，第 33 脚 PA12 = USB_DP。全速的 1.5 kΩ 上拉接在 D+ 和 3.3 V 之间，也就是第 33 脚这一侧。接到第 32 脚上，主机不会按这颗全速设备来认。见 [DS5319 Rev 20 表 5](#source-ds5319-usbcan)。片内上拉只有手册印出了阻值才写进出处卡。没印出阻值时，图上的 1.5 kΩ 仍是罗盘里的数。

这颗料的 USB 是全速设备，不是主机。12 Mbit/s 是它的全速档。低速 1.5 Mbit/s 不是它的工作模式。见 [RM0008](#source-rm0008-usb)。

设备描述符长度 `0x12`，共 18 字节。`bMaxPacketSize0` 是 64。VID 是 `0x1209`，PID 是 `0x0001`。这是本仓库实验号。`0x0483/0x5740` 不是这份描述符。配置集合的 `wTotalLength` 是 `0x0043`，即 67，不是 18。`bMaxPower = 0x32`，单位 2 mA，所以是 100 mA。见 [本仓库例程](#source-project-examples)。

全速批量和中断的上限都是 64 字节。1023 只属于全速等时。例程的通知端点是 8 字节，批量端点是 64 字节。8 没有超出 64 的上限。

PA11/PA12 的 CAN 默认功能在第 13 章已经移走。本图只画 USB。`USB_LP_CAN1_RX0` 与 CAN 接收是同一条中断，两个例程不要编在一起。

## 关键插图

<p align="center">
  <img src="../assets/diagrams/sample-14-usb-enum.svg" width="760" alt="全速要 48 MHz；D+ 上拉在第 33 脚；这份描述符是 18 字节设备加 67 字节配置集合，VID/PID 是 0x1209/0x0001">
  <br><sub>▲ 自绘。STM32F103C8T6。正常路径是 USBPRE = 0、48 MHz、第 33 脚 D+ 上的 1.5 kΩ、18 字节和 67 字节。失败路径是 USBPRE = 1，时钟变成 72 MHz。0x0483/0x5740 不是这份描述符。出处是 [RM0008](#source-rm0008-rcc)、[DS5319](#source-ds5319-usbcan) 和 [usb-cdc](#source-project-examples)。</sub>
</p>

<p align="center">
  <img src="../assets/gif/usb-48m.gif" width="640" alt="D+ 被拉高，时钟是 48 MHz，随后是 18 字节和 67 字节">
  <br><sub>▲ 网页和公众号辅图。只播放正常路径：D+ 上拉、48 MHz、18 字节、67 字节。印刷以静态主图为准。72 MHz 和接错的上拉不在这条 GIF 上。</sub>
</p>

`usb-enumeration.svg` 留作辅图。

## 时序或状态

| 项目 | 值 | 对错 |
| --- | --- | --- |
| `USBPRE = 0` | 48 MHz | 正常。72 / 1.5 = 48 |
| `USBPRE = 1` | 72 MHz | 失败 |
| 设备描述符 | 长度 18，`bMaxPacketSize0` 64 | VID `0x1209`，PID `0x0001` |
| 配置集合 | `wTotalLength` 67，即 `0x0043` | `bMaxPower` `0x32` = 100 mA |
| 包长 | 批量和中断上限 64 | 1023 只属于等时。通知端点 8 是允许的 |
| 脚位 | 第 32 脚 DM，第 33 脚 DP | 上拉在 DP。接到 DM 不是这条正常路径 |

## 坑与出处卡

| 现象 | 原因 | 处理 | 出处 | 该来源允许支持的主张 |
| --- | --- | --- | --- | --- |
| 设备管理器里描述符请求失败 | USB 时钟不是 48 MHz | `USBPRE` 保持 0 | [RM0008](#source-rm0008-rcc) | `USBPRE=0` 时 72 MHz ÷1.5 = 48 MHz。`USBPRE=1` 得到 72 MHz |
| 主机完全看不到设备 | 上拉不在 D+ | 上拉接在第 33 脚 D+，不要接到 DM。阻值用罗盘里的 1.5 kΩ | [DS5319](#source-ds5319-usbcan) | 第 32 脚 PA11 的复用含 USB_DM，第 33 脚 PA12 的复用含 USB_DP。这一行不证明上拉阻值。罗盘已写 1.5 kΩ |
| 枚举到的是别人的 VID | 抄了 ST 例程那一对 | 用本仓库的 `0x1209/0x0001`。`0x0483/0x5740` 不是这份描述符 | [本仓库例程](#source-project-examples) | `examples/usb-cdc` 的设备描述符是 18 字节。VID/PID 是 `0x1209/0x0001`。PID 只给实验板占位 |
| 配置集合长度和字节数对不上 | 把 18 写成了总长 | `wTotalLength` 写成 67 | [本仓库例程](#source-project-examples) | 配置描述符里的总长是 `0x0043`。`bMaxPower` 的 `0x32` 是 100 mA |
| 中断或批量端点写成 1023 | 用了等时的上限 | 全速这两类的上限是 64。1023 只给等时 | [本仓库例程](#source-project-examples) | 例程批量端点是 64 字节，通知端点是 8 字节 |
| 和 CAN 例程链在一起，接收中断串了 | 两条例程共用一条向量 | 两个例程分开。CAN 不要留在 PA11/PA12 | [RM0008](#source-rm0008-usb) | 向量名以 snapshot 里印出的为准。默认是 `USB_LP_CAN1_RX0`。这颗料的 USB 是设备，不是主机 |
```

英文四块用 `../../assets/diagrams/sample-14-usb-enum.svg` 和 `../../assets/gif/usb-48m.gif`。图注写 `Drawn for this book`。必须出现 `not a host` 和 `not this descriptor`。四块不要出现 `10 ms`，也不要出现 `90`。

```markdown
## Principle and boundary

The clock and the descriptor are fixed on STM32F103C8T6. The USB clock is copied from chapter file 02 and from the compass. The PLL is 72 MHz. `USBPRE = 0` divides by 1.5, so the USB clock is 48 MHz. `USBPRE = 1` does not divide, so the USB clock is 72 MHz and the host fails while reading the descriptor. See [RM0008](#source-rm0008-rcc). Do not redraw the clock tree.

Pin 32 PA11 = USB_DM. Pin 33 PA12 = USB_DP. The full-speed 1.5 kΩ pull-up sits between D+ and 3.3 V, on the pin 33 side. Tied to pin 32, the host does not see this full-speed device. See [DS5319 Rev 20 Table 5](#source-ds5319-usbcan). An on-chip pull-up enters a source card only when the manual prints the resistance. Until then, the 1.5 kΩ on the figure is the compass value.

USB on this part is a full-speed device, not a host. 12 Mbit/s is its full-speed rate. 1.5 Mbit/s low speed is not its working mode. See [RM0008](#source-rm0008-usb).

The device descriptor length is `0x12`, 18 bytes. `bMaxPacketSize0` is 64. VID is `0x1209` and PID is `0x0001`. That pair is this repository's experiment id. `0x0483/0x5740` is not this descriptor. The configuration set `wTotalLength` is `0x0043`, which is 67, not 18. `bMaxPower = 0x32` is in units of 2 mA, so it is 100 mA. See [examples in this repo](#source-project-examples).

The full-speed bulk and interrupt ceiling is 64 bytes. 1023 belongs only to full-speed isochronous. The example notification endpoint is 8 bytes and the bulk endpoints are 64. 8 does not exceed the ceiling of 64.

Chapter file 13 already moved the default CAN function off PA11/PA12. This figure draws only USB. `USB_LP_CAN1_RX0` is the same interrupt as CAN receive. Do not build the two examples together.

## Key figures

<p align="center">
  <img src="../../assets/diagrams/sample-14-usb-enum.svg" width="760" alt="Full speed needs 48 MHz. The D+ pull-up is on pin 33. This descriptor is an 18-byte device plus a 67-byte configuration set, VID/PID 0x1209/0x0001.">
  <br><sub>▲ Drawn for this book. STM32F103C8T6. The normal path is USBPRE = 0, 48 MHz, 1.5 kΩ on D+ at pin 33, 18 bytes, and 67 bytes. The failure path is USBPRE = 1, and the clock becomes 72 MHz. 0x0483/0x5740 is not this descriptor. Sources: [RM0008](#source-rm0008-rcc), [DS5319](#source-ds5319-usbcan), and [usb-cdc](#source-project-examples).</sub>
</p>

<p align="center">
  <img src="../../assets/gif/usb-48m.gif" width="640" alt="D+ is pulled up, the clock is 48 MHz, then 18 bytes and 67 bytes">
  <br><sub>▲ Auxiliary figure for the web and for posts. It plays only the normal path: the D+ pull-up, 48 MHz, 18 bytes, and 67 bytes. Print from the static figure. 72 MHz and the pull-up on the wrong pin are not on this GIF.</sub>
</p>

`usb-enumeration.svg` stays as an auxiliary figure.

## Timing or state

| Item | Value | Right or wrong |
| --- | --- | --- |
| `USBPRE = 0` | 48 MHz | Normal. 72 / 1.5 = 48 |
| `USBPRE = 1` | 72 MHz | Failure |
| Device descriptor | length 18, `bMaxPacketSize0` 64 | VID `0x1209`, PID `0x0001` |
| Configuration set | `wTotalLength` 67, which is `0x0043` | `bMaxPower` `0x32` = 100 mA |
| Packet length | bulk and interrupt ceiling 64 | 1023 is isochronous only. A notification endpoint of 8 is allowed |
| Pins | pin 32 is DM, pin 33 is DP | The pull-up is on DP. On DM it is not this normal path |

## Pitfalls and source cards

| What you see | Why | What to do | Source | Claim this source may support |
| --- | --- | --- | --- | --- |
| Device Manager fails the descriptor request | The USB clock is not 48 MHz | Keep `USBPRE` at 0 | [RM0008](#source-rm0008-rcc) | `USBPRE=0` makes 72 MHz ÷ 1.5 = 48 MHz. `USBPRE=1` yields 72 MHz |
| The host does not see the device at all | The pull-up is not on D+ | Tie the pull-up to D+ on pin 33, not to DM. Use the compass value 1.5 kΩ | [DS5319](#source-ds5319-usbcan) | Pin 32 PA11 includes USB_DM. Pin 33 PA12 includes USB_DP. This row does not prove the pull-up resistance. The compass already says 1.5 kΩ |
| Enumeration shows someone else's VID | The ST example pair was copied | Use this repository's `0x1209/0x0001`. `0x0483/0x5740` is not this descriptor | [examples in this repo](#source-project-examples) | `examples/usb-cdc` has an 18-byte device descriptor. VID/PID is `0x1209/0x0001`. The PID is only a placeholder for the experiment board |
| The configuration length does not match the bytes | 18 was written as the total length | Write `wTotalLength` as 67 | [examples in this repo](#source-project-examples) | The total length in the configuration descriptor is `0x0043`. `bMaxPower` `0x32` is 100 mA |
| An interrupt or bulk endpoint is set to 1023 | That ceiling belongs to isochronous | The ceiling for those two classes at full speed is 64. 1023 is isochronous only | [examples in this repo](#source-project-examples) | The example bulk endpoint is 64 bytes and the notification endpoint is 8 bytes |
| Linked with the CAN example, the receive interrupt is shared | The two examples use one vector | Keep the examples apart. Do not leave CAN on PA11/PA12 | [RM0008](#source-rm0008-usb) | The vector name is the one printed in the snapshot. The default is `USB_LP_CAN1_RX0`. USB on this part is a device, not a host |
```

- [ ] **Step 5: 只改第 14 章罗盘**

两份 manifest 的第 14 章 `sources` 改成测试里的 `compass`。中文键 `14-USB.md`。英文键 `14-usb.md`。不要新建 source 对象。不要改 `rm0008-rcc`、`usb20`、`project-examples`、`ds5319-usbcan`、`rm0008-usb` 的字段。`sources` 字典的末尾仍是 Task 6 停下的 `rm0008-usb`。

- [ ] **Step 6: 运行测试并提交**

Run: `python3 stm32-book/tests/test_batch5_chapters.py Batch5UsbChapterTests -v`

Expected: OK。

```bash
git add docs/14-USB.md docs/en/14-usb.md stm32-book/manifest.json stm32-book/manifest-en.json stm32-book/tests/test_batch5_chapters.py
git commit -m "book: 加厚第 14 章并把 48 MHz 和 67 字节钉在同一笔账"
```

### Task 8: Thicken chapter 15 in both languages

**Files:**
- Modify: `docs/15-FreeRTOS入门.md`
- Modify: `docs/en/15-freertos.md`
- Modify: `stm32-book/manifest.json` 与 `stm32-book/manifest-en.json`（追加 `freertos-syscall`，并改第 15 章罗盘）
- Modify: `stm32-book/tests/test_batch5_chapters.py`
- Test: `stm32-book/tests/test_batch5_chapters.py`

**Interfaces:**
- Consumes: `rtos_prio()` 与 `rtos-tick.gif`。Task 6 结束时 `sources` 末尾是 `rm0008-usb`。已有 `project-examples`。
- Produces: 中英第 15 章各一套四块。新 id `freertos-syscall` 接在 `rm0008-usb` 后面。五个新 id 的最终顺序是 `rm0008-flash`、`rm0008-can`、`ds5319-usbcan`、`rm0008-usb`、`freertos-syscall`。视频块字节不变。

英文锚点是 `## 📌 Learning goals`。英文核心标题是 `## 🧠 Core ideas`。英文旧坑标题是 `## ⚠️ Pitfalls and troubleshooting`。

- [ ] **Step 1: 把章节断言加进测试**

在 `Batch5UsbChapterTests` 之后追加：

```python
class Batch5RtosChapterTests(unittest.TestCase):
    def test_rtos_chapters_have_four_blocks_and_the_same_numbers(self) -> None:
        zh_path = ROOT / "docs" / "15-FreeRTOS入门.md"
        en_path = ROOT / "docs" / "en" / "15-freertos.md"
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
        self.assertIn("## 📌 Learning goals", en)
        self.assertIn("## 🧠 Core ideas", en)
        self.assertIn("TIM4", zh)
        self.assertIn("TIM4", en)
        self.assertNotIn("改为 **TIMx**", zh)
        self.assertNotIn("改成 TIMx", zh)
        self.assertNotIn("改 TIMx", zh)
        self.assertNotIn("to **TIMx**", en)
        self.assertNotIn("to TIMx", en)
        self.assertIn("没有 FPU", zh)
        self.assertIn("no FPU", en)
        self.assertNotIn("选带 FPU 的移植（", zh)
        self.assertNotIn("Use the port that includes the FPU", en)
        zh_blocks = zh.split("## 原理与边界", 1)[1].split("## 📌 学习目标", 1)[0]
        en_blocks = en.split("## Principle and boundary", 1)[1].split("## 📌 Learning goals", 1)[0]
        for blocks in (zh_blocks, en_blocks):
            for token in (
                "1000",
                "0x50",
                "128",
                "512",
                "192",
                "768",
                "256",
                "1024",
                "TIM4",
                "13",
                "GROUP_4",
                "#source-project-examples",
                "#source-freertos-syscall",
            ):
                self.assertIn(token, blocks)
            self.assertNotIn("167 ns", blocks)
            self.assertNotIn("17.2", blocks)
        self.assertIn("大于等于 5", zh_blocks)
        self.assertIn("5 or a larger number", en_blocks)
        self.assertIn("../assets/diagrams/sample-15-rtos-prio.svg", zh)
        self.assertIn("../../assets/diagrams/sample-15-rtos-prio.svg", en)
        self.assertIn("../assets/gif/rtos-tick.gif", zh)
        self.assertIn("../../assets/gif/rtos-tick.gif", en)
        zh_key = zh.split("## 关键插图", 1)[1].split("## 时序或状态", 1)[0]
        en_key = en.split("## Key figures", 1)[1].split("## Timing or state", 1)[0]
        self.assertLess(zh_key.index("sample-15-rtos-prio.svg"), zh_key.index("rtos-tick.gif"))
        self.assertLess(en_key.index("sample-15-rtos-prio.svg"), en_key.index("rtos-tick.gif"))
        self.assertIn("自绘", zh_key)
        self.assertIn("Drawn for this book", en_key)
        self.assertNotIn("示意图", zh_key)
        lock = json.loads(
            (ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch5-12-13-14-15-lock.json").read_text(
                encoding="utf-8"
            )
        )
        for path, now in ((zh_path, zh), (en_path, en)):
            rel = path.relative_to(ROOT).as_posix()
            baseline = subprocess.check_output(
                ["git", "-C", str(ROOT), "show", f"{lock['baseline']}:{rel}"],
            ).decode("utf-8")
            marker = "<!-- video:ch15 -->"
            end = "<!-- /video:ch15 -->"
            self.assertEqual(
                baseline.split(marker, 1)[1].split(end, 1)[0],
                now.split(marker, 1)[1].split(end, 1)[0],
            )
        zh_manifest = json.loads((ROOT / "stm32-book" / "manifest.json").read_text(encoding="utf-8"))
        en_manifest = json.loads((ROOT / "stm32-book" / "manifest-en.json").read_text(encoding="utf-8"))
        compass = [
            "freertos-priority",
            "pm0056",
            "project-examples",
            "freertos-syscall",
        ]
        self.assertEqual(compass, zh_manifest["chapter_guides"]["15-FreeRTOS入门.md"]["sources"])
        self.assertEqual(compass, en_manifest["chapter_guides"]["15-freertos.md"]["sources"])
        self.assertEqual(
            [
                "rm0008-flash",
                "rm0008-can",
                "ds5319-usbcan",
                "rm0008-usb",
                "freertos-syscall",
            ],
            list(zh_manifest["sources"])[-5:],
        )
        listed = json.loads(
            (ROOT / "docs" / "superpowers" / "plans" / "2026-10-25-batch5-12-13-14-15-source-list.json").read_text(
                encoding="utf-8"
            )
        )
        by_id = {item["id"]: item for item in listed["absorb"]}
        card_zh = zh_manifest["sources"]["freertos-syscall"]
        card_en = en_manifest["sources"]["freertos-syscall"]
        for key in ("url", "snapshot", "license"):
            self.assertEqual(by_id["freertos-syscall"][key], card_zh[key])
            self.assertEqual(card_zh[key], card_en[key])
        self.assertEqual("2026-10-25", card_zh["accessed"])
        self.assertEqual("MIT", card_zh["license"])
        self.assertEqual(by_id["freertos-syscall"]["title_zh"], card_zh["title"])
        self.assertEqual(by_id["freertos-syscall"]["title_en"], card_en["title"])
        self.assertEqual(
            "第 15 章的 0x50、字栈方向和互斥量。4 位优先级时 5 左移 4 位是 0x50。任务优先级数值更大的先跑。xTaskCreate 的深度单位是字。互斥量有优先级继承，二值信号量没有。不覆盖第 28 章。不把 17.2% 写进来。",
            card_zh["scope"],
        )
        self.assertEqual(
            "Chapter file 15 for 0x50, the word-stack direction, and mutexes. With 4 priority bits, 5 shifted left by 4 is 0x50. A numerically larger task priority runs first. The xTaskCreate depth is in words. A mutex has priority inheritance and a binary semaphore does not. Does not cover chapter file 28. Does not bring in 17.2 percent.",
            card_en["scope"],
        )
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python3 stm32-book/tests/test_batch5_chapters.py Batch5RtosChapterTests -v`

Expected: FAIL，中文稿还没有 `## 原理与边界`。

- [ ] **Step 3: 把时基写成 TIM4，把 FPU 标成作废，并删掉旧坑表**

中文视频块以外，做这五处替换。实验节里的「64 字」留在实验，不删。

把 `CubeMX：SYS → Timebase Source 改为 **TIMx**` 换成 `CubeMX：SYS → Timebase Source 改为 **TIM4**`。

把 `从 **SysTick 改成 TIMx**` 换成 `从 **SysTick 改成 TIM4**`。

把 `Timebase Source 改 TIMx` 换成 `Timebase Source 改 TIM4`。

把 `改 TIMx 时基` 换成 `改 TIM4 时基`。

在「数值越大优先级越高」那一节的结论段落后面加上：

```markdown
STM32F103C8T6 是 Cortex-M3，没有 FPU。选带 FPU 的移植在这颗料上作废。
```

删掉从 `## ⚠️ 常见坑与排查` 到 `## 🧪 动手实验` 之前的整节。删掉之后，正文里不再有「选带 FPU 的移植（」。

英文做对应替换。

把 `change it to **TIMx**` 换成 `change it to **TIM4**`。

把 `from **SysTick to TIMx**` 换成 `from **SysTick to TIM4**`。

把 `Change Timebase Source to TIMx` 换成 `Change Timebase Source to TIM4`。

把 `Move the timebase to TIMx` 换成 `Move the timebase to TIM4`。

在任务优先级和 NVIC 方向相反的那一段落后面加上：

```markdown
STM32F103C8T6 is a Cortex-M3 and has no FPU. A port built for an FPU is void on this part.
```

删掉从 `## ⚠️ Pitfalls and troubleshooting` 到 `## 🧪 Hands-on labs` 之前的整节。删掉之后不再有 `Use the port that includes the FPU`。

- [ ] **Step 4: 在学习目标之前插入四块**

中文：

```markdown
## 原理与边界

这一章的节拍和 FromISR 只钉在订货号 STM32F103C8T6 上。分组跟第 04 章同一笔：`NVIC_PRIORITYGROUP_4`，4 位抢占，0 位子优先级。不把 167 ns 搬进来。

`configTICK_RATE_HZ = 1000`，一个 tick 是 1 ms。短于 1 ms 的期限不是内核保证。SysTick 归内核。HAL 的时基是 TIM4，这是 `examples/freertos-task` 的 README 已经写明的那一只。两家都占 SysTick 时，`HAL_Delay` 卡住。见 [本仓库例程](#source-project-examples)。

任务优先级数值大的先跑。KEY 是 2，LED 和 UART 是 1，同时就绪时先跑 KEY。把任务优先级当成 NVIC、以为 1 比 2 更优先，是失败路径。NVIC 仍是数值小的更优先。空闲任务是 0。这颗料没有 FPU。

`5 << (8 − 4) = 0x50`。调用 FromISR 的中断，抢占优先级数值要大于等于 5。例程把 `EXTI0` 设成 5。设成 0 会停在 `configASSERT`。数值 4 同样过急。见 [FreeRTOS Kernel V11.3.2](#source-freertos-syscall)。

`xTaskCreate` 的栈深度是字，一字 4 字节。LED 128 字 = 512 字节。KEY 192 字 = 768 字节。UART 256 字 = 1024 字节。把 128 当成 128 字节，是失败旁注。

先干 3 ms 再 `vTaskDelay(10)`，从调用时再等 10 个 tick，周期接近 13 ms。`vTaskDelayUntil` 的 10 ms 把周期钉在 10 ms。保护共享资源用互斥量，有优先级继承。二值信号量没有继承。heap_4 会合并相邻空闲块。不搬第 28 章的预算。

## 关键插图

<p align="center">
  <img src="../assets/diagrams/sample-15-rtos-prio.svg" width="760" alt="一个 tick 是 1 ms；任务优先级 2 先于 1；128 字是 512 字节；FromISR 的数值优先级要大于等于 5">
  <br><sub>▲ 自绘。STM32F103C8T6。正常路径是 SysTick 1 ms、HAL 时基 TIM4、优先级 2 在跑、优先级 1 在等、LED 栈 128 字 = 512 字节、EXTI0 抢占优先级 5。失败路径是同一条 EXTI 的抢占优先级写成 0，调用 FromISR 后停在 configASSERT。出处是 [FreeRTOS Kernel V11.3.2](#source-freertos-syscall) 和 [freertos-task](#source-project-examples)。</sub>
</p>

<p align="center">
  <img src="../assets/gif/rtos-tick.gif" width="640" alt="节拍每 1 ms 走一格，优先级 2 占着 CPU，128 字等于 512 字节">
  <br><sub>▲ 网页和公众号辅图。只播放正常路径：1 ms 一格，优先级 2 在跑，优先级 1 在等，128 words = 512 bytes。印刷以静态主图为准。configASSERT 和 SysTick 冲突不在这条 GIF 上。</sub>
</p>

`freertos-scheduler.svg` 留作辅图。

## 时序或状态

| 对象 | 数值 | 谁先走 |
| --- | --- | --- |
| tick | 1000 Hz | 1 ms |
| 任务 | 优先级 2 与优先级 1 | 2 先于 1。方向和 NVIC 相反 |
| 栈 | 128 字 = 512 字节 | KEY 192 字 = 768 字节。UART 256 字 = 1024 字节 |
| 中断 | 数值 5 可以调用 FromISR | 数值 0 停在 `configASSERT`。`0x50 = 5 << 4` |
| 时基 | 内核用 SysTick | HAL 用 TIM4 |
| 延时 | 工作 3 ms 再 `vTaskDelay(10)` | 周期接近 13 ms。`vTaskDelayUntil` 的 10 ms 仍是 10 ms |

## 坑与出处卡

| 现象 | 原因 | 处理 | 出处 | 该来源允许支持的主张 |
| --- | --- | --- | --- | --- |
| `HAL_Delay` 卡住，或调度器起不来 | HAL 和内核抢 SysTick | HAL 时基改到 TIM4 | [本仓库例程](#source-project-examples) | `examples/freertos-task` 的 README 把时基源写成 TIM4 |
| 一进中断就停在 `configASSERT` | 抢占优先级数值比 5 更小 | `EXTI0` 写成 5 或更靠后的数 | [FreeRTOS](#source-freertos-syscall) | 4 位优先级时，5 左移 4 位是 `0x50`。数值更小的中断不得调用 FromISR |
| 优先级 1 的任务压过优先级 2 | 把任务优先级当成了 NVIC | 任务优先级数值大的先跑 | [FreeRTOS](#source-freertos-syscall) | 任务优先级数值更大的先跑 |
| 例程里 KEY 没有压过 LED | 两个任务写成了同一个优先级 | KEY 写 2，LED 和 UART 写 1 | [本仓库例程](#source-project-examples) | `examples/freertos-task` 里 KEY 的任务优先级是 2，LED 和 UART 是 1 |
| 栈说明书写 128，一打印就溢出 | 把字当成了字节 | 128 的单位是字，等于 512 字节 | [本仓库例程](#source-project-examples) | LED 128 字，KEY 192 字，UART 256 字 |
| 按键中断一进来就断言 | EXTI 抢占优先级过急 | `EXTI0` 的抢占优先级写成 5 | [本仓库例程](#source-project-examples) | 例程把 `EXTI0` 的抢占优先级设成 5 |
| 两个任务的串口叠在一起 | 用二值信号量保护了资源 | 用互斥量 | [FreeRTOS](#source-freertos-syscall) | 互斥量有优先级继承。二值信号量没有 |
| 周期越来越长 | `vTaskDelay(10)` 不包含调用前已经花掉的时间 | 固定周期用 `vTaskDelayUntil` | [FreeRTOS](#source-freertos-syscall) | 一个 tick 是 1 ms 时，调用前已经花掉的时间不包含在 `vTaskDelay` 里 |
```

英文四块路径用 `../../assets/...`。图注写 `Drawn for this book`。必须出现 `no FPU`、`TIM4`、`5 or a larger number`。四块不要出现 `167 ns` 和 `17.2`。

```markdown
## Principle and boundary

The tick and FromISR are fixed on STM32F103C8T6. The group matches chapter file 04: `NVIC_PRIORITYGROUP_4`, 4 preemption bits, and 0 subpriority bits. Do not import 167 ns.

`configTICK_RATE_HZ = 1000`, so one tick is 1 ms. A deadline shorter than 1 ms is not a kernel guarantee. SysTick belongs to the kernel. The HAL time base is TIM4, the timer already named in the `examples/freertos-task` README. If both sides take SysTick, `HAL_Delay` sticks. See [examples in this repo](#source-project-examples).

A numerically larger task priority runs first. KEY is 2. LED and UART are 1. When both are ready, KEY runs first. Treating task priority like the NVIC, and expecting 1 to beat 2, is the failure path. The NVIC still treats a smaller number as more urgent. The idle task is 0. This part has no FPU.

`5 << (8 − 4) = 0x50`. An interrupt that calls FromISR needs a preemption priority number greater than or equal to 5, that is 5 or a larger number. The example sets `EXTI0` to 5. Setting it to 0 stops in `configASSERT`. The number 4 is also too urgent. See [FreeRTOS Kernel V11.3.2](#source-freertos-syscall).

The `xTaskCreate` depth is in words, and one word is 4 bytes. LED is 128 words = 512 bytes. KEY is 192 words = 768 bytes. UART is 256 words = 1024 bytes. Reading 128 as 128 bytes is the failure note.

Do 3 ms of work and then `vTaskDelay(10)`, and the call waits another 10 ticks, so the period is near 13 ms. `vTaskDelayUntil` of 10 ms keeps the period at 10 ms. A mutex protects a shared resource and has priority inheritance. A binary semaphore does not. heap_4 coalesces adjacent free blocks. Do not import the budget from chapter file 28.

## Key figures

<p align="center">
  <img src="../../assets/diagrams/sample-15-rtos-prio.svg" width="760" alt="One tick is 1 ms. Task priority 2 runs before priority 1. 128 words are 512 bytes. FromISR needs a numeric priority of 5 or a larger number.">
  <br><sub>▲ Drawn for this book. STM32F103C8T6. The normal path is a 1 ms SysTick, HAL time base TIM4, priority 2 running, priority 1 waiting, an LED stack of 128 words = 512 bytes, and EXTI0 preemption priority 5. The failure path writes that EXTI preemption priority as 0 and stops in configASSERT on FromISR. Sources: [FreeRTOS Kernel V11.3.2](#source-freertos-syscall) and [freertos-task](#source-project-examples).</sub>
</p>

<p align="center">
  <img src="../../assets/gif/rtos-tick.gif" width="640" alt="The tick advances 1 ms at a time, priority 2 holds the CPU, and 128 words equal 512 bytes">
  <br><sub>▲ Auxiliary figure for the web and for posts. It plays only the normal path: 1 ms steps, priority 2 running, priority 1 waiting, 128 words = 512 bytes. Print from the static figure. configASSERT and the SysTick clash are not on this GIF.</sub>
</p>

`freertos-scheduler.svg` stays as an auxiliary figure.

## Timing or state

| Object | Value | Who goes first |
| --- | --- | --- |
| tick | 1000 Hz | 1 ms |
| Tasks | priority 2 and priority 1 | 2 before 1. The direction is the opposite of the NVIC |
| Stacks | 128 words = 512 bytes | KEY 192 words = 768 bytes. UART 256 words = 1024 bytes |
| Interrupt | number 5 may call FromISR | number 0 stops in `configASSERT`. `0x50 = 5 << 4` |
| Time base | the kernel uses SysTick | HAL uses TIM4 |
| Delay | 3 ms of work, then `vTaskDelay(10)` | the period is near 13 ms. `vTaskDelayUntil` of 10 ms stays 10 ms |

## Pitfalls and source cards

| What you see | Why | What to do | Source | Claim this source may support |
| --- | --- | --- | --- | --- |
| `HAL_Delay` sticks, or the scheduler does not start | HAL and the kernel both want SysTick | Move the HAL time base to TIM4 | [examples in this repo](#source-project-examples) | The `examples/freertos-task` README names TIM4 as the time base |
| The interrupt stops in `configASSERT` | The preemption number is smaller than 5 | Write `EXTI0` as 5 or a larger number | [FreeRTOS](#source-freertos-syscall) | With 4 priority bits, 5 shifted left by 4 is `0x50`. A numerically smaller interrupt must not call FromISR |
| A priority 1 task runs over a priority 2 task | Task priority was treated like the NVIC | A numerically larger task priority runs first | [FreeRTOS](#source-freertos-syscall) | A numerically larger task priority runs first |
| KEY does not run ahead of LED in the example | Both tasks were given the same priority | Write KEY as 2, and LED and UART as 1 | [examples in this repo](#source-project-examples) | In `examples/freertos-task`, KEY's task priority is 2 and LED and UART are 1 |
| The stack note says 128 and a print overflows | A word was read as a byte | 128 is in words, which is 512 bytes | [examples in this repo](#source-project-examples) | LED is 128 words, KEY is 192 words, UART is 256 words |
| The key interrupt asserts as soon as it is entered | The EXTI preemption priority is too urgent | Write the `EXTI0` preemption priority as 5 | [examples in this repo](#source-project-examples) | The example sets the `EXTI0` preemption priority to 5 |
| Two tasks interleave on the UART | A binary semaphore was used to protect the resource | Use a mutex | [FreeRTOS](#source-freertos-syscall) | A mutex has priority inheritance. A binary semaphore does not |
| The period grows | `vTaskDelay(10)` does not include the time already spent before the call | Use `vTaskDelayUntil` for a fixed period | [FreeRTOS](#source-freertos-syscall) | When one tick is 1 ms, time already spent before the call is not inside `vTaskDelay` |
```

- [ ] **Step 5: 追加 freertos-syscall**

把 `freertos-syscall` 追加到两份 manifest 的 `sources` 末尾。`url`、`snapshot`、`license` 从清单原样复制。`license` 是 `MIT`。`accessed` 是 `2026-10-25`。`title` 和 `authority` 用清单的中英字段。`scope` 用本任务测试里的两句。第 15 章罗盘改成测试里的 `compass`。不改 `freertos-1132`、`freertos-priority`、`pm0056`、`project-examples` 的字段。

- [ ] **Step 6: 运行测试并提交**

Run: `python3 stm32-book/tests/test_batch5_chapters.py Batch5RtosChapterTests -v`

Expected: OK。

```bash
git add docs/15-FreeRTOS入门.md docs/en/15-freertos.md stm32-book/manifest.json stm32-book/manifest-en.json stm32-book/tests/test_batch5_chapters.py
git commit -m "book: 加厚第 15 章并把时基钉在 TIM4"
```

### Task 9: Register the batch, bump 1.3.0, keep the ledgers

**Files:**
- Modify: `CREDITS.md`
- Modify: `stm32-book/manifest.json` 与 `stm32-book/manifest-en.json` 的 `version` 与 `date`
- Modify: `stm32-book/revisions.json`
- Modify: `stm32-book/README.md`
- Modify: `stm32-book/tests/test_build.py`
- Test: `stm32-book/tests/test_build.py`

**Interfaces:**
- Consumes: Task 5 到 Task 8 已经写进 manifest 的五个新 id。日期是 `2026-10-25`，不另取。当前版本断言仍是 1.2.9。`test_visual_polish_version_is_1_2_0` 里 `entries[0]` 到 `entries[9]` 依次是 1.2.9 海报、1.2.8 密度、1.2.7 浅色、1.2.6 封面、1.2.5 令牌、1.2.4 排版、1.2.3、1.2.2、1.2.1、1.2.0。
- Produces: 两份 manifest 的 `version` 都是 `1.3.0`，`date` 都是 `2026-10-25`。`revisions.json` 的 `entries[0].version` 是 `1.3.0`。原来的 1.2.9 海报说明整段挪到 `entries[1]`，后面每一条各挪后一格，字符串不改。`0x271` 断言、`167 ns` 断言和出版书签长度 44 的断言还在。

- [ ] **Step 1: 先改版本断言，让测试失败**

在 `stm32-book/tests/test_build.py` 里只改当前版断言。不要删 `0x271`、`167 ns`、`会上手的几笔账`、`Numbers to reconcile before changing family`、`Channels, descriptors, and fault registers`，也不要改 `self.assertEqual(44, len(outline))`。

把

```python
versions = ("1.2.9", "1.2.8", "1.2.7", "1.2.6", "1.2.5", "1.2.4", "1.2.3", "1.2.2", "1.2.1", "1.2.0", "1.1.1", "1.1.0", "1.0.8", "1.0.7", "1.0.6", "1.0.5", "1.0.4", "1.0.3", "1.0.2", "1.0.1", "1.0.0")
```

改成

```python
versions = ("1.3.0", "1.2.9", "1.2.8", "1.2.7", "1.2.6", "1.2.5", "1.2.4", "1.2.3", "1.2.2", "1.2.1", "1.2.0", "1.1.1", "1.1.0", "1.0.8", "1.0.7", "1.0.6", "1.0.5", "1.0.4", "1.0.3", "1.0.2", "1.0.1", "1.0.0")
```

在 `self.assertLess(history.index(">1.2.9<"), history.index(">1.2.8<"))` 之前加一行：

```python
self.assertLess(history.index(">1.3.0<"), history.index(">1.2.9<"))
```

把修订列表期望的首项从 `"1.2.9"` 改成在它前面加上 `"1.3.0"`。其余版本顺序不动。

把 `self.assertEqual("1.2.9", manifest["version"])` 改成 `self.assertEqual("1.3.0", manifest["version"])`。

把两处 `self.assertIn("<strong>v1.2.9</strong>", html)` 改成 `self.assertIn("<strong>v1.3.0</strong>", html)`。

`test_visual_polish_version_is_1_2_0` 里，把取条目的十行换成：

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
```

`posters`、`density`、`entry`、`cover`、`tokens`、`typography`、`batch4`、`batch3`、`guide`、`previous` 下面已有的中英字符串一句都不要改。它们只是改去读后移的那一格。`posters["version"]` 仍断言 `"1.2.9"`。`density["version"]` 仍断言 `"1.2.8"`。后面的版本号断言同样不动。

把这一函数里对当前 manifest 的两行改成 1.3.0：

```python
        self.assertEqual("1.3.0", self.manifest["version"])
        self.assertEqual("2026-10-25", self.manifest["date"])
        self.assertEqual("1.3.0", english["version"])
        self.assertEqual("2026-10-25", english["date"])
```

在 `posters` 的断言之前加上 `batch5` 的断言：

```python
        self.assertEqual("1.3.0", batch5["version"])
        self.assertEqual("2026-10-25", batch5["date"])
        self.assertEqual(batch5["date"], self.manifest["date"])
        self.assertEqual(batch5["date"], english["date"])
        self.assertEqual(
            [
                "第 12 章写上中容量 1 KB 页，APP 从 0x08004800 起、长度 0xB800，跳转要装入第 0 字和第 1 字。第 13 章写上预分频 9、8 个时间份额是 500 kbit/s，预分频 8 且 10 个时间份额是 450 kbit/s，工作脚是 PB8/PB9。",
                "第 14 章写上 USBPRE=0 得到 48 MHz，描述符是 18 字节和 67 字节，VID/PID 是 0x1209/0x0001。第 15 章写上 1 ms 节拍、128 字等于 512 字节、FromISR 的数值优先级要大于等于 5，HAL 时基是 TIM4。",
            ],
            batch5["zh"],
        )
        self.assertEqual(
            [
                "Chapter file 12 records medium-density 1 KB pages, an application at 0x08004800 for 0xB800 bytes, and a jump that loads word 0 and word 1. Chapter file 13 records prescaler 9 and eight time quanta as 500 kbit/s, prescaler 8 and ten time quanta as 450 kbit/s, and the working pins PB8 and PB9.",
                "Chapter file 14 records USBPRE=0 as 48 MHz, an 18-byte device descriptor and a 67-byte configuration set, and VID/PID 0x1209/0x0001. Chapter file 15 records a 1 ms tick, 128 words as 512 bytes, FromISR only at numeric priority 5 or lower urgency, and the HAL time base TIM4.",
            ],
            batch5["en"],
        )
```

README 断言改成：

```python
        self.assertIn("当前版本：**v1.3.0 · 2026-10-25**", readme)
        self.assertIn("版本号已经是 1.3.0。", readme)
        self.assertIn("也不要把 1.2.8 的产物标成 1.2.9。", readme)
        self.assertIn("也不要把 1.2.9 的产物标成 1.3.0。", readme)
        self.assertIn("打 tag `v1.3.0`", readme)
        self.assertNotIn("当前版本：**v1.2.9", readme)
        self.assertNotIn("打 tag `v1.2.9`", readme)
```

原来对 1.2.0 到 1.2.8 那一串「也不要把」的断言留着。不要删 `样式来自` 那一句。

- [ ] **Step 2: 运行版本测试，确认失败**

Run: `python3 stm32-book/tests/test_build.py BookBuildTests.test_revision_file_lists_1_0_0_through_manifest_version -v`

Expected: FAIL，修订列表的首项仍是 `1.2.9`。

- [ ] **Step 3: 写 1.3.0**

两份 manifest 的 `version` 改为 `1.3.0`，`date` 保持 `2026-10-25`。不要改 `sources` 里已有对象的字段，也不要改这一批五个新对象的 snapshot。

在 `stm32-book/revisions.json` 的 `entries` 数组最前面插入：

```json
{
  "version": "1.3.0",
  "date": "2026-10-25",
  "zh": [
    "第 12 章写上中容量 1 KB 页，APP 从 0x08004800 起、长度 0xB800，跳转要装入第 0 字和第 1 字。第 13 章写上预分频 9、8 个时间份额是 500 kbit/s，预分频 8 且 10 个时间份额是 450 kbit/s，工作脚是 PB8/PB9。",
    "第 14 章写上 USBPRE=0 得到 48 MHz，描述符是 18 字节和 67 字节，VID/PID 是 0x1209/0x0001。第 15 章写上 1 ms 节拍、128 字等于 512 字节、FromISR 的数值优先级要大于等于 5，HAL 时基是 TIM4。"
  ],
  "en": [
    "Chapter file 12 records medium-density 1 KB pages, an application at 0x08004800 for 0xB800 bytes, and a jump that loads word 0 and word 1. Chapter file 13 records prescaler 9 and eight time quanta as 500 kbit/s, prescaler 8 and ten time quanta as 450 kbit/s, and the working pins PB8 and PB9.",
    "Chapter file 14 records USBPRE=0 as 48 MHz, an 18-byte device descriptor and a 67-byte configuration set, and VID/PID 0x1209/0x0001. Chapter file 15 records a 1 ms tick, 128 words as 512 bytes, FromISR only at numeric priority 5 or lower urgency, and the HAL time base TIM4."
  ]
}
```

修订说明只写这四章，用文件名前缀。不写第 28 章，不把标题写成「第 13 章」去代替文件 `12`。

`stm32-book/README.md` 的当前版本句改为：

```markdown
当前版本：**v1.3.0 · 2026-10-25**。中文整书和英文整书共用这一版号。GitHub Release 仍要等这次提交进入 `main` 且 Book CI 产出四份文件之后，由有权限的人另行处理。
```

把「版本号已经是 1.2.9。」改成「版本号已经是 1.3.0。」。在「也不要把 1.2.8 的产物标成 1.2.9。」之后加上「也不要把 1.2.9 的产物标成 1.3.0。」。第三步的「在该提交上打 tag `v1.2.9`」改成「在该提交上打 tag `v1.3.0`」。这一步仍不创建 tag，也不创建 Release。

- [ ] **Step 4: 在 CREDITS.md 增加 v1.3.0 小节，并改正张数**

第一节表格里「静态框图（18 张）」换成「静态框图（22 张）」。只有 `assets/diagrams/sample-12-iap-vectors.svg` 真的存在时才写成 23 张，并在实施 PR 说明里写明拆图原因。

「光栅动画（16 个 GIF）」换成「光栅动画（20 个 GIF）」。不要重跑已有 16 个 GIF。20 是 `BUILDERS` 的键数，不是 `*-zh.gif` 的张数。

第六节已有的小节标题和表都保留，含「第 01、07、10、11 章（v1.2.3）」。在该节末尾追加：

```markdown
### 第 12、13、14、15 章（v1.3.0）

第 12、13、14、15 章用改写吸收补了同样的四块。吸收的是事实，用本书的句子重写，并配上自绘静态图。手册正文、官方插图、USB-IF 原文、ISO 原文和厂商数据手册不放进仓库。

| 作品 | 许可证 | 用在 | 链接 |
| --- | --- | --- | --- |
| RM0008 Rev 21（2021-02），闪存、bxCAN、USB 设备 | ST 文档条款；只链接并改写事实，不转载手册 | 第 12 章 1 KB 页和两把钥匙；第 13 章 500 kbit/s 与总线关闭；第 14 章全速设备和 USB_LP_CAN1_RX0 | https://www.st.com/resource/en/reference_manual/rm0008-stm32f101xx-stm32f102xx-stm32f103xx-advanced-arm-based-32-bit-mcus-stmicroelectronics.pdf |
| DS5319 Rev 20（2025-07），表 5 | ST 文档条款；只链接并改写事实，不转载手册 | 第 13 章第 45、46 脚和第 5、6 脚；第 14 章第 32、33 脚 | https://www.st.com/resource/en/datasheet/stm32f103c8.pdf |
| FreeRTOS Kernel V11.3.2 | MIT | 第 15 章 0x50、字栈和互斥量。不吸收网站正文 | https://github.com/FreeRTOS/FreeRTOS-Kernel/releases/tag/V11.3.2 |
| 本仓库 `examples/iap-bootloader`、`examples/can-bxcan`、`examples/usb-cdc`、`examples/freertos-task` | MIT | 第 12 章 0xB800；第 13 章预分频 9 和左移 5；第 14 章 0x1209/0x0001；第 15 章 TIM4 和 128/192/256 字 | https://github.com/zhuguang-ZFG/STM32/tree/main/examples |
```

- [ ] **Step 5: 运行整套测试和构建检查**

Run: `python3 -m unittest discover stm32-book/tests -v`

Expected: OK。`test_sample_chapters.py`、`test_batch2_chapters.py`、`test_batch3_chapters.py`、`test_batch4_chapters.py` 仍然通过。

Run: `python3 stm32-book/build_html.py --check && python3 stm32-book/build_html.py --lang en --check`

Expected: 两个命令都退出码 0。构建出的 HTML 里有 `v1.3.0`，并且 `id="source-rm0008-flash"`、`id="source-rm0008-can"`、`id="source-ds5319-usbcan"`、`id="source-rm0008-usb"`、`id="source-freertos-syscall"` 都在。

Run: `python3 tools/check_assets.py`

Expected: 退出码 0，输出含 `全部通过`。

- [ ] **Step 6: Commit**

```bash
git add CREDITS.md stm32-book/manifest.json stm32-book/manifest-en.json stm32-book/revisions.json stm32-book/README.md stm32-book/tests/test_build.py
git commit -m "book: 第 12、13、14、15 章登记来源并把整书标成 1.3.0"
```

### Task 10: Scope gate, then stop

**Files:**
- 不新增文件。这一任务只核对 diff。核对失败时，只撤销越界改动，不顺手加厚别的章，也不去改 CSS。

**Interfaces:**
- Consumes: Task 1 到 Task 9 的提交。
- Produces: 一份只含第 12、13、14、15 章加厚的 diff。用户复审之前，实施 PR 保持打开。没有 tag，没有 Release。Book CI 变绿不等于可以 squash 合入。

- [ ] **Step 1: 核对 diff 的路径**

Run:

```bash
git diff --name-only origin/main...HEAD
```

Expected: 只出现这些路径。顺序可以不同。`sample-12-iap-vectors.svg` 只有在 Task 3 真的拆图时才允许出现。

```text
CREDITS.md
assets/README.md
assets/diagrams/sample-12-iap-map.svg
assets/diagrams/sample-13-can-bit.svg
assets/diagrams/sample-14-usb-enum.svg
assets/diagrams/sample-15-rtos-prio.svg
assets/gif/can-500k.gif
assets/gif/iap-jump.gif
assets/gif/rtos-tick.gif
assets/gif/usb-48m.gif
docs/12-Flash与IAP升级.md
docs/13-CAN总线.md
docs/14-USB.md
docs/15-FreeRTOS入门.md
docs/en/12-flash-iap.md
docs/en/13-can.md
docs/en/14-usb.md
docs/en/15-freertos.md
docs/superpowers/plans/2026-10-25-batch5-12-13-14-15-lock.json
docs/superpowers/plans/2026-10-25-batch5-12-13-14-15-source-list.json
docs/superpowers/plans/2026-10-25-classic-encyclopedia-batch5-12-13-14-15.md
stm32-book/README.md
stm32-book/manifest-en.json
stm32-book/manifest.json
stm32-book/revisions.json
stm32-book/tests/test_batch5_chapters.py
stm32-book/tests/test_batch5_sources.py
stm32-book/tests/test_build.py
tools/gen_gifs.py
tools/gen_sample_figures.py
tools/scan_batch5_chapters.py
```

`docs/superpowers/plans/2026-10-25-classic-encyclopedia-batch5-12-13-14-15.md` 只在「先合并了本计划」的历史上出现。若实施分支从本计划提交切开，它会留在 diff 里，这是允许的。它不是章节正文。

`stm32-book/build_html.py`、`stm32-book/styles/book.css`、`stm32-book/styles/tokens.json`、`stm32-book/book/`、`docs/CONTENT_GUIDE.md`、`docs/en/CONTENT_GUIDE.md`、`assets/video/`、`tools/gen_narrated.py`、样本锁定、Batch2 锁定、Batch3 锁定、Batch4 锁定，以及其余章节都不在这份列表里。

- [ ] **Step 2: 核对附录、样式、海报和已经加厚的章没有被卷进来**

Run:

```bash
git diff origin/main...HEAD -- stm32-book/build_html.py stm32-book/styles/book.css stm32-book/styles/tokens.json stm32-book/book/A-工程深读.md stm32-book/book/D-术语表.md stm32-book/book/en/A-uart-dma.md stm32-book/book/en/D-glossary.md assets/video tools/gen_narrated.py docs/00-如何学习STM32.md docs/01-开发环境搭建.md docs/28-嵌入式系统与RTOS生态.md
```

Expected: 无输出。

Run:

```bash
git diff --name-only origin/main...HEAD -- docs/16-低功耗设计.md docs/17-调试与性能优化.md examples/iap-bootloader examples/can-bxcan examples/usb-cdc examples/usb-hid examples/freertos-task assets/animations/flash-iap.svg assets/animations/can-arbitration.svg assets/animations/usb-enumeration.svg assets/animations/freertos-scheduler.svg assets/diagrams/sample-02-clock-tree.svg assets/diagrams/sample-04-exception-stack.svg assets/diagrams/sample-07-i2c-addr.svg
```

Expected: 无输出。

用锁定文件里的 `baseline` 核对已有来源对象没有被改字段。把 `REV` 设成锁定文件的 `baseline`，然后运行：

```bash
python3 - << 'PY'
import json, subprocess
from pathlib import Path
root = Path(".").resolve()
lock = json.loads(Path("docs/superpowers/plans/2026-10-25-batch5-12-13-14-15-lock.json").read_text(encoding="utf-8"))
rev = lock["baseline"]
frozen = [
    "rm0008", "ds5319", "rm0008-rcc", "ds5319-clock", "ds5319-i2c", "ds5319-swd",
    "pm0075-rdp", "pm0056", "pm0056-vector", "pm0056-nvic", "project-examples",
    "rm0090", "usb20", "freertos-priority", "freertos-1132", "an2606", "an3965",
]
for name in ("stm32-book/manifest.json", "stm32-book/manifest-en.json"):
    old = json.loads(subprocess.check_output(["git", "show", f"{rev}:{name}"], text=True))
    new = json.loads(Path(name).read_text(encoding="utf-8"))
    for source_id in frozen:
        assert old["sources"][source_id] == new["sources"][source_id], source_id
print("frozen sources unchanged")
PY
```

Expected: 打印 `frozen sources unchanged`，退出码 0。

在 `stm32-book/build_html.py` 里确认 `display_chapter_number` 仍是文件名前缀加 1。本批 diff 必须为空，所以这一条只是读，不改。

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

不要运行 `gh release create`，不要 `git tag`，不要打 `v1.2.9` 或 `v1.3.0`。

- [ ] **Step 5: 停在用户复审**

实施 PR 的说明里写明：只加厚了文件 `12`、`13`、`14`、`15` 的中英八份；静态主图是 `sample-12-iap-map.svg`、`sample-13-can-bit.svg`、`sample-14-usb-enum.svg`、`sample-15-rtos-prio.svg`；短 GIF 是辅图。第 12 章是中容量 1 KB 页，APP 从 `0x08004800` 起、长度 `0xB800`。第 13 章预分频 9、8 个时间份额是 500 kbit/s，预分频 8 且 10 个时间份额是 450 kbit/s，工作脚是 PB8/PB9。第 14 章 `USBPRE=0` 得到 48 MHz，描述符是 18 字节和 67 字节，VID/PID 是 `0x1209/0x0001`。第 15 章是 1 ms 节拍、128 字等于 512 字节、FromISR 的数值优先级要大于等于 5，HAL 时基是 TIM4。若脚号、片内上拉、USB 向量名、CAN 重映射、过滤器的 5 位、FreeRTOS 库优先级，或第 12 章拆图和清单不同，说明里写明差异。

请用户看构建出的中英 HTML 里的这四章：四块是否都在、关掉动画之后主图是否仍能指出失败、`#source-` 是否点得到附录 E 的卡片。

第 12 章要能指出的失败是「钥匙反序，或末页写成 `0x0801FC00`，或 `VTOR` 仍为 0」。第 13 章要能指出的失败是「预分频 8 且 10 个时间份额，500 kbit/s 变成 450 kbit/s」。第 14 章要能指出的失败是「`USBPRE = 1`，USB 时钟是 72 MHz」。第 15 章要能指出的失败是「抢占优先级 0 调用了 FromISR」。

用户书面接受之前：

- 不为 `00`–`11` 或 `16`–`28` 开加厚 PR。
- 不加图目录或表目录。
- 不改 `stm32-book/build_html.py`，不改 `book.css`，不改显示章号，不改 PDF 书签深度。
- 不改 `assets/video/`，不重录旁白，不重画 29 张讲解海报。
- 不打 `v1.3.0` 的 tag，不创建 GitHub Release。
- 不把 Book CI 变绿当成可以自动 squash 合入。人接受之前，实施 PR 保持打开。
- 不预选文件 `16` 或 `28`。下一批仍是 4 章，到下一次设计再锁。

这一步没有新的提交。若 Step 1 到 Step 3 发现越界文件，撤销那些文件里的越界改动后再提交一次，提交说明写明撤回了哪一处，然后仍停在这里。

## 对照设计规格

| 设计规格里的要求 | 落在 |
| --- | --- |
| 只加厚 12、13、14、15，中英一起，四块标题各一次 | Task 5、Task 6、Task 7、Task 8、Task 10 |
| 英文第 13、14 章旧坑标题是文件里的 `## ⚠️ Pitfalls`，不先改长 | Task 1、Task 6、Task 7 |
| 静态主图，正常路径和失败路径，不用 `Svg.footer()`，小于 60 KB | Task 3 |
| 第 12 章超过 60 KB 才拆 `sample-12-iap-vectors.svg`，静态框图改为 23 张 | Task 3、Task 9 |
| 短 GIF 只是辅图，帧数 3 到 12，不改已有 16 个 BUILDERS 的像素 | Task 4 |
| 第 12 章中容量 1 KB、`0xB800`、两把钥匙、两字、`0x0801FC00` 作废 | Task 5 |
| 第 13 章 500 kbit/s 与 450 kbit/s，PB8/PB9，PD0/PD1 存在，60 Ω 不是电缆阻抗 | Task 6 |
| 第 14 章 48 MHz 与 72 MHz，18 与 67，`0x1209/0x0001`，上拉在 D+ | Task 7 |
| 第 15 章 1 ms、`0x50`、128 字 = 512 字节、TIM4、没有 FPU，不写 167 ns 和 17.2% | Task 8 |
| 脚号、片内上拉、向量名、重映射、过滤器 5 位、库优先级按印出的文字改 snapshot | Task 2 |
| 新 id 只追加五个；已有 id 一个字段都不改 | Task 2、Task 5、Task 6、Task 8、Task 10 |
| 版本 1.3.0 · 2026-10-25，不打 tag，不发 Release。本计划提交不升版本 | Task 9、Task 10 |
| 不改 CSS、海报、`assets/video/`、旁白、附录 A、附录 D、`build_html.py`、更早的锁定和其余章 | Task 10 |
| 书签仍是 44，`0x271` 与 `167 ns` 断言仍在，样本测试和 Batch2、Batch3、Batch4 测试不放宽 | Task 9 |
| CI 变绿后停下来等人复审，不自动合入 | Task 10 |
| 不预选文件 16 或 28 | Task 10 |

## 执行交接

计划写在 `docs/superpowers/plans/2026-10-25-classic-encyclopedia-batch5-12-13-14-15.md`。本计划 PR 只增加这一份文件。实施时二选一，而且要等这份计划被人接受之后再开实施 PR：

1. Subagent-Driven（推荐）：每个任务一个新的子代理，任务之间复核。必用 superpowers:subagent-driven-development。
2. Inline Execution：在同一个会话里按 superpowers:executing-plans 分批做，每批停下来复核。

无论哪一种，Task 10 都停在人复审。人接受之前不合入。实施 PR 的目标版本是 1.3.0 · 2026-10-25。这一份计划本身不升版本，不改章节正文，不提交 SVG 或 GIF。




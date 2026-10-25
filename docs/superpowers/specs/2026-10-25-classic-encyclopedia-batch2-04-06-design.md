# 第 04 与第 06 章加厚设计

日期：2026-10-25  
状态：已批准，待第 04 章与第 06 章实施  
基线：`main` 上的整书 **v1.1.0**（`e8afafcfc0ed95a705915eef981dd6e609c84ab4`，PR #21，2026-10-25）  
上一份设计：[2026-10-25-classic-encyclopedia-thicken-design.md](2026-10-25-classic-encyclopedia-thicken-design.md)（PR #18）。样本实施计划是 `docs/superpowers/plans/2026-10-25-classic-encyclopedia-sample-chapters.md`（PR #20）。  
本文件只记录这一批的设计。它不改章节正文，不画新图，不改 `stm32-book/` 构建，不升版本号，不打 tag，不发布 Release。

## 背景

v1.1.0 已经按四块模板加厚了第 00 章和第 03 章，并停下来等过复审。复审之后这一批只加厚另外两章：**04 中断与 NVIC**、**06 串口 UART**。中文和英文一起写。文件名仍是 `docs/04-中断与NVIC.md`、`docs/en/04-interrupts-nvic.md`、`docs/06-串口UART.md`、`docs/en/06-uart.md`。

读者看到的章号已经是第 1–29 章：`display_chapter_number` 把文件名前缀加 1，所以文件 `04` 在书里是第 5 章，文件 `06` 是第 7 章。源文件的一级标题继续带 `04` 和 `06`。这一批不改这个加 1，也不把标题改成「第 5 章」。

对照 v1.1.0 核对过的事实：

1. **这两章还没有四块。** 第 00 章和第 03 章在视频块之后、学习目标之前，已经有 `## 原理与边界`、`## 关键插图`、`## 时序或状态`、`## 坑与出处卡`（英文是 `Principle and boundary`、`Key figures`、`Timing or state`、`Pitfalls and source cards`）。第 04 章和第 06 章仍从学习目标写起，坑还在 `## ⚠️ 常见坑与排查`，坑表没有 `#source-`。
2. **第 04 章的图还不能当印刷主图。** 章内是 `assets/animations/nvic-interrupt-flow.svg`、`assets/animations/gpio-input-interrupt.svg` 和 `assets/diagrams/interrupt-priority.svg`。前两张是动画，第三张是抢占与子优先级的简笔仲裁。没有一张同时画出 8 个寄存器的入栈/出栈，以及「优先级写错所以更高的请求进不来」。罗盘已经写了入栈大约 12 个 HCLK、72 MHz 时约 167 ns、HAL 默认 `NVIC_PRIORITYGROUP_4`。附录 D「换系列之前先对的账」把同一笔账钉在第 04 章和 PM0056 上。正文的尾链只有一句「省去出栈再入栈」，没有和「谁有权抢占」分开。
3. **第 06 章的主图也还是动画。** 章首是 `assets/animations/uart-frame.svg`，帧格式小节另有 `assets/gif/uart-bits.gif`。GIF 能播放逐位，印刷时不能代替一张带采样点和帧错误的静态图。罗盘和附录 D 写的是：USART1 在 APB2，72 MHz、16 倍过采样、115200，`USARTDIV = 39.0625`，BRR = `0x271`，分频误差是 0；一位约 8.68 µs，8N1 一帧约 86.8 µs。附录 A 第 7 节写明：第 06 章的表现在把 39.0625 和 0.16% 放在同一行；大约 0.16% 属于 USART2、36 MHz、BRR `0x138`，也属于把 39.0625 的小数位丢掉、只用 39 的那种算法。这一批改的是第 06 章那张表，不改附录 A，也不改附录 D。
4. **RM0008 的 USART 没有 OVER8。** 第 06 章现在写「F1/F4 支持 OVER8」。RM0008 Rev 21 第 27 章里，`USART_CR1` 偏移 `0x0C`，位 31:14 保留；`USART_BRR` 偏移 `0x08`，小数是 `DIV_Fraction[3:0]`，分频按 16 倍。8 倍过采样是带 OVER8 的系列（F4 的 RM0090）上的另一句话。在 STM32F103C8T6 上，这句话作废。
5. **许可门已经在样本里跑通过一次。** 允许吸收的是 ST 手册里的事实（自己的话重写），以及 MIT、BSD-2-Clause、BSD-3-Clause、ISC、CC BY 4.0、CC BY 3.0、CC0。GPL、LGPL、CC BY-NC、CC BY-ND、保留所有权利、未写许可的材料只留链接。Apache-2.0 不在允许名单里，不吸收 CMSIS 正文。`sources` 只追加。样本新增的 `rm0008-boot`、`rm0008-gpio`、`ds5319-gpio` 一个字段都不改。
6. **两份社区 UART 条目已经在清单里，但还不是坑卡。** `majerle-uart` 冻结在 commit `c242589d766eada3ad1d795630f2b1c2482a2af8`。该 commit 的 `LICENSE` 是 MIT。`st-uart-idle` 是 ST 社区帖，清单里的许可是「链接引用」，不吸收句子。`stm32cube-f4` 冻结在 tag `v1.28.3`（commit `94cae6e83f00e276a11957e7833c01ac3d0bd7af`），HAL 是 BSD-3-Clause。这三条的 manifest 对象都不改写，坑卡只去链接它们。
7. **第 01 章和第 02 章的既有图不动。** `boot-sequence.svg` 带 `BOOT0`，`clock-tree.svg` 与 `memory-map.svg` 带 MHz。它们不是这一批的主图，也不换成新的编号图。

## 目标与非目标

### 目标

- 只把第 04 章和第 06 章加厚到和第 00、03 章相同的四块密度。中文和英文一起写完。
- 每章一张可印刷的静态主图：正常路径和失败路径都在图上，信号名、脚位和文档号是真的。另加一条短 GIF，只做网页和公众号辅图。
- 数字钉在已经冻结的 RM/DS/PM 和附录 D 已有的格子上。第 06 章那张自相矛盾的误差表改到和附录 D 同一笔账。
- 新出处追加进两份 manifest 的 `sources`。章内坑卡使用 `#source-...`。`CREDITS.md` 第六节记下这一批改写吸收了什么。
- 实施合入时把整书从 1.1.0 升到 **1.1.1**。中英文共用这个版本号。这一批不打 tag，不创建 Release。

### 非目标

- 不加厚除 04、06 以外的任何章，含 00、01、02、03、05 和 07–28。不改这几章的英文。
- 不重选样本。不改 `docs/superpowers/plans/2026-10-25-sample-chapter-lock.json`，不改 `2026-10-25-sample-source-list.json`，不改 `tools/scan_sample_chapters.py` 的打分规则去再选一次章。
- 不改 `docs/superpowers/specs/2026-10-25-classic-encyclopedia-thicken-design.md`，不改样本实施计划。
- 不实现 v1.1.0 的 GitHub Release，也不打 `v1.1.0` 或 `v1.1.1` 的 tag。
- 不改 `stm32-book/build_html.py`。出版书签仍是现在的 44 条（分部、章、附录、版本与修订、主题索引），不把新的二级标题收进书签。
- 不改附录 A 的既有契约，不改附录 D 三套账的算术，不手改 `stm32-book/book/E-参考资料.md` 或英文对应文件。附录 E 的卡片仍由 `sources` 生成。
- 不替换、不重画第 01 章和第 02 章已有的图，也不删除第 04、06 章已有的 `nvic-interrupt-flow.svg`、`gpio-input-interrupt.svg`、`interrupt-priority.svg`、`uart-frame.svg`、`uart-bits.gif`。新主图是加进去的，不是覆盖。
- 不把厂商手册、官方插图、社区原文或 MaJerle 的源码放进仓库。不新做讲解视频，不改 `assets/video/`。
- 不加图目录或表目录，不加第 30 章，不改 `docs/00`–`28` 的文件名。

## 来源与许可

四层用法和上一份设计相同。这一批写死要用的材料和明确不复制的部分。

允许写进正文的，仍按这个顺序：

1. ST 的 RM、DS、PM：只吸收事实，用自己的话写，附文档号和可点击的入口。不粘贴段落，不描官方图。
2. MIT、BSD-2-Clause、BSD-3-Clause、ISC、CC BY 4.0、CC BY 3.0、CC0：可以改写教学要点。许可证不强制署名时，本书仍署名。
3. 其他许可证：只留链接。含 GPL、LGPL、CC BY-NC、CC BY-ND、Apache-2.0、保留所有权利、未写许可的帖子和视频。

权威数字以第 1 层和附录 D 已有格子为准。社区材料只支持「这个坑有人踩过」。帖子里的寄存器值，要在 RM/DS 上重新钉住之后才能进「原理与边界」或「时序或状态」。钉不住的，出处卡的主张写成「经验线索，未升格为规范」，并且这一行不引入新的寄存器值。

### 追加的来源 id

新 id 只追加在两份 `sources` 对象的末尾。已有 id 的标题、URL、snapshot、许可、scope 都不改。中英两份的 `url`、`snapshot`、`license`、`accessed` 用同一串字符；`title`、`authority`、`scope` 用对应语言。章罗盘的 `sources` 数组在原有 id 之后追加新 id，不删除已有 id。来源清单的 `absorb` 必须含 `rm0008-exti`、`pm0056-nvic`、`rm0008-usart`、`ds5319-usart`。`rm0090-usart-over8` 只有在 snapshot 里写进了 OVER8 位号时才出现。

| 新 id | 冻结点 | 用在 | 不复制 |
| --- | --- | --- | --- |
| `rm0008-exti` | RM0008 Rev 21，2021-02。第 10 章 EXTI；AFIO 的 `EXTICR`。PDF 与样本的 RM0008 链接相同 | 第 04 章。EXTI 线按脚号共用；F1 映射要开 AFIO 时钟；`EXTI_PR` 要清 | 不把 9.2.7 写成 EXTICR。9.2.7 已由 `rm0008-gpio` 钉成 `GPIOx_LCKR`。EXTICR 的节号以 Rev 21 印出来的 AFIO 寄存器节为准 |
| `pm0056-nvic` | PM0056。入口用 `https://www.st.com/resource/en/programming_manual/pm0056-stm32f10xxx-cortex-m3-programming-manual-stmicroelectronics.pdf`。打不开时改用文档中心上真正打开这份手册的 URL，两份 manifest 写同一个 | 第 04 章。8 寄存器入栈、尾链不改变抢占权、PRIMASK 挡不住 NMI | 不改已有 `pm0056`。那条 scope 是 CFSR/HFSR 地址。不把 167 ns 写成 ISR 正文的预算 |
| `rm0008-usart` | RM0008 Rev 21 第 27 章。接收在 27.3.3，`USART_BRR` 在 27.6.3。若这份修订的目录把 BRR 印成别的小节，snapshot 改用印出来的小节，算式不变 | 第 06 章。16 倍采样、BRR、IDLE、帧错误 | 不粘贴 27.3.3，不描官方采样图 |
| `ds5319-usart` | DS5319 Rev 20，2025-07，图 8 与表 5。PDF 与 `ds5319-gpio` 相同 | 第 06 章。LQFP48 第 30 脚 PA9、第 31 脚 PA10 | 不描引脚图。不把 PB6/PB7 的重映射说成复位后的默认脚 |
| `rm0090-usart-over8` | 只在 8 倍那一句需要位号时才追加。冻结一份写明 USART OVER8 的 RM0090 修订 | 第 06 章边界里「换到 F4 才成立」的那一句 | 不改已有 `rm0090`。那条 scope 是 Flash 扇区和 DMA。F103 上不算 8 倍的 BRR |

中断方面，若许可门找不到 MIT、BSD 或 CC BY/CC0 的社区例程，来源清单里的社区列表就是空的。空列表不挡住加厚。不改去吸收 libopencm3，也不吸收未写许可的博客。找到一份时，冻结完整 commit，读该 commit 的 `LICENSE` 再决定；许可证不在允许名单里就只留链接。

### 沿用、但不改写对象的 id

| 已有 id | 这一批怎么用 |
| --- | --- |
| `majerle-uart` | 冻结 commit 的许可证是 MIT。坑卡改写它已经登记的要点：持续 DMA 接收时，应用读到 DMA 写位置为止，缓冲区不是一条拍平的帧。用自己的话写。不粘贴函数，不把该仓库的寄存器值写成新规范。`CREDITS.md` 第六节写上作品名、MIT 和这条 commit URL。manifest 里那条对象保持「仓库 LICENSE」原文 |
| `st-uart-idle` | 坑卡保留一行，链接这个 id。主张只写「经验线索，未升格为规范」：有人报告过 HT 与 IDLE 挨着来。这一行不引入新的寄存器值或微秒数。帖子里的句子不进正文。若冻结的 Cube 例程自己写出了相邻触发，规范性的那一行另链 `#source-stm32cube-f4`，论坛这一行仍只是线索 |
| `stm32cube-f4` | HAL 是 BSD-3-Clause。坑卡改写 `Size` 的要点：循环 DMA 的 `Size` 是写位置，不是这一次的增量。范围停在 tag `v1.28.3` 那个 F446 例程，不把它的引脚说成 F103 |
| `freertos-priority` | 仍是链接引用。第 04 章最多用现有罗盘那句：裸机优先级不等于第 15 章的 FromISR 约束。不把 `0x50` 写进第 04 章。`0x50` 留在第 15 章和附录 D |
| `rm0008`、`pm0056`、`ds5319`、`rm0090` | 不改。新事实走上表的新 id |

出处卡的字段仍是现有附录 E 的一套：`title`、`authority`、`url`、`snapshot`、`accessed`、`license`、`scope`。`url` 必须是 `https://`。章内第四块每一行只有一个主张，并带一个 `#source-`。一行写清现象、原因、处理、链接、该来源允许支持的主张。

`CREDITS.md` 第六节现在的标题是「样本章的改写吸收（v1.1.0）」。这一批在该节下面加一个小节「第 04 章与第 06 章（v1.1.1）」，保留 v1.1.0 的表。新表只列作品名、许可证、用在哪、链接。不贴社区原文。

## 锁定

章号已经由批准的设计锁死，不再按「谁更薄」重选。

实施开始时仍做一次核对扫描，只读文件 `04` 和 `06` 的中英四份。扫描确认两件事：四块标题还不存在；旧的「常见坑」标题还在。结果写到新文件 `docs/superpowers/plans/2026-10-25-batch2-04-06-lock.json`，带上运行时的 `git rev-parse HEAD`。不覆盖样本的锁定文件。若扫描发现四块已经有人写过，停下来，不叠第二套标题。

来源清单写到 `docs/superpowers/plans/2026-10-25-batch2-04-06-source-list.json`，字段沿用样本清单：`chapters` 是 `["04", "06"]`，`absorb` 里每一条有 `license_class`、`url`、`do_not_copy`、`points`。`license_class` 只允许 `ST-facts-restated`、`MIT`、`BSD-2-Clause`、`BSD-3-Clause`、`ISC`、`CC BY 4.0`、`CC BY 3.0`、`CC0`。许可字符串里不得出现 `GPL`、`LGPL`、`CC BY-NC`、`CC BY-ND`、`All rights reserved`。清单可以先于 manifest 提交；登记以 manifest 为准。

## 章节加厚模板

四块插在视频块之后、学习目标之前，和第 03 章相同。标题不加表情符号，中英各出现一次：

| 块 | 中文标题 | 英文标题 | 这一块要写完的事 |
| --- | --- | --- | --- |
| 1 | `## 原理与边界` | `## Principle and boundary` | 结论钉在哪颗订货号、哪路时钟、哪一版手册；换系列时哪一句作废 |
| 2 | `## 关键插图` | `## Key figures` | 静态主图在前，图注带关键数字和文档号。短 GIF 跟在后面，图注标明辅图 |
| 3 | `## 时序或状态` | `## Timing or state` | 一张能算回去的表。时间或状态迁移和主图是同一笔账 |
| 4 | `## 坑与出处卡` | `## Pitfalls and source cards` | 旧坑表里钉得住的行挪到这里。每行一个 `#source-` |

保留学习目标、硬件与接线、代码实现、动手实验、相关资源，以及英文的对应标题。保留 `## 🧠 核心原理`，用来放还没被四块收走的教程骨架。第 00 章和第 03 章就是这样留的。和四块或附录 D 冲突的数字，就地改成同一笔账，不保留两套说法。`## ⚠️ 常见坑与排查` 和英文 `## ⚠️ Pitfalls and troubleshooting` 删掉，不留空标题。

视频块、旁白和已有动画图留在原处。主图不放进 `<!-- video:` 块。代码仍按 `docs/CONTENT_GUIDE.md`：HAL，参数用宏。这一批不新开可烧录工程，保留 `examples/exti-key/` 和 `examples/uart-dma-idle/`。

中英的订货号、文档号、寄存器名、脚位和算式一致。英文可以更短，不能少一块，也不能少一个关键数字。

## 第 04 章写什么

订货号是 STM32F103C8T6。时钟沿用附录 D：SYSCLK = HCLK = 72 MHz。分组沿用罗盘和附录 D：HAL 默认 `NVIC_PRIORITYGROUP_4`，4 位抢占、0 位子优先级。数值越小，逻辑优先级越高。这三句整格照抄，不另算一个「大约 12 周期」的新数。

### 原理与边界

三句边界都要写完，并且写明哪一句在换分组或换屏蔽寄存器时作废。

- **抢占和子优先级。** 抢占优先级更高（数值更小）的异常可以打断正在执行的、抢占更低的 ISR。子优先级只在多份请求已经同时挂起时决定谁先被响应，不能用来嵌套。`GROUP_4` 的子优先级位数是 0，`HAL_NVIC_SetPriority` 的子优先级参数在这个分组下不产生嵌套。要看见子优先级起作用，分组不能是 `GROUP_4`。分组一改，原来的数值不再表示同一级抢占。附录 D 已经把「改了分组还用旧的抢占级去比谁能嵌套」写成误读，正文沿用这句，不改附录。
- **尾链。** 退出时若已有挂起异常，硬件可以省掉一部分出栈再入栈。尾链减少开销，不改变谁有权抢占。低优先级不会因为尾链插进高优先级的 ISR。术语表里「尾链打开后，低优先级也能插入高优先级」是误解，正文不把它写成机制。尾链的周期数只有在 `pm0056-nvic` 点名的那一节里印着数字时才写；没印着就不编一个周期数，图上只画出「没有发生第二次嵌套入栈」。不把这个周期数补进附录 D。
- **不可屏蔽。** `PRIMASK` 关掉可配置优先级的中断，NMI 和 HardFault 仍能进入。`FAULTMASK` 再挡住 HardFault，仍留 NMI。`BASEPRI` 只挡住优先级数值大于等于阈值的那一截。NMI 不参加 EXTI0 和 TIM2 那种抢占比较。第 02 章的 CSS 进 NMI 只作交叉引用，不在这一章重写时钟树。

裸机这套配置不自动满足第 15 章的 FromISR 约束。这句话链到已有的 `#source-freertos-priority`，不引入 `0x50`。

EXTI 线按脚号共用：PA0 和 PB0 都在 EXTI0 上，不能同时做外部中断。F1 上改端口要先开 AFIO 时钟，再写 `EXTICR`。这句只在 F1 上成立。

### 关键插图

主图文件 `assets/diagrams/sample-04-exception-stack.svg`，由 `tools/gen_sample_figures.py` 追加一个函数生成，和现有 `boot_state`、`gpio_led` 一样调用 `_credit()`，不调用 `Svg.footer()`。`Svg.footer()` 会印上「自绘矢量动画」，样本测试已经禁止这几个字出现在静态主图里。

图上同时有这两条路径：

- **正常路径。** 分组是 `NVIC_PRIORITYGROUP_4`。TIM2 以抢占 2 正在执行，EXTI0（PA0 下降沿，`EXTI0_IRQn`）以抢占 1、子优先级 0 打断它。硬件入栈 8 个寄存器，图上按从高地址到低地址写成 xPSR、PC、LR、R12、R3、R2、R1、R0，入栈后的 SP 指向 R0。旁边写附录 D 的原句：大约 12 个 HCLK，72 MHz 时 `12 / 72e6 ≈ 167 ns`，不含 ISR 正文。然后取向量、执行 ISR、出栈返回。
- **失败路径。** 把 EXTI0 写成和 TIM2 相同的抢占优先级（都是 1），子优先级仍按 0 和 1 分开写。子优先级不同也不嵌套。EXTI0 保持挂起，等正在执行的 ISR 退出；退出时可以尾链进去，但图上标明没有第二次嵌套入栈。这就是「优先级写错，更高的请求进不来」。把 EXTI0 的抢占数值写成比 TIM2 更大，是出处卡里的另一行，不在这张图上再画第三条路径。
- **NMI 不走这条失败。** 图上用一条短标注：`PRIMASK = 1` 时 EXTI0 和 TIM2 都进不来，NMI 仍然进入。不要把 NMI 画成被 NVIC 抢占字段挡住。

信号和名字使用 `PA0`、`EXTI0`、`EXTI_PR`、`EXTI0_IRQn`、`TIM2_IRQn`、`PRIMASK`、`NMI`。图注写「自绘」，写出 8 个寄存器名、167 ns、`GROUP_4`，以及 `pm0056-nvic` 与 `rm0008-exti` 的文档号。替代文本写出结论：抢占 1 可以打断抢占 2；抢占同为 1 时后来的请求不能嵌套。不写「示意图」。

章首的 `nvic-interrupt-flow.svg` 和简笔 `interrupt-priority.svg` 留作辅图。关键插图这一节要写明：不播放它们，主图仍然能指出失败发生在「抢占被写成同一级」那一段。

### 时序或状态

一张表，列对齐主图。至少包括：分组 `GROUP_4`；TIM2 抢占 2 正在执行；EXTI0 抢占 1 到达并入栈；12 HCLK / 约 167 ns；ISR；出栈。失败行：两者抢占都是 1，状态留在挂起，尾链只发生在退出之后。另一行：`PRIMASK = 1`，可配置中断不进入，NMI 仍进入。表里的 167 ns 与附录 D 同一笔，不改成别的纳秒数。

### 坑与出处卡

至少这些行，每行一个主张：

| 现象 | 处理方向 | 链接 | 允许的主张 |
| --- | --- | --- | --- |
| 子优先级更小，却打断不了正在跑的 ISR | 改抢占级，不要改子优先级来嵌套 | `#source-pm0056-nvic` | 同抢占不能嵌套；`GROUP_4` 没有子优先级位 |
| 按键中断打不断定时器 | 让 EXTI0 的抢占数值小于 TIM2 | `#source-pm0056-nvic` | 数值越小越优先；写反了就嵌套失败 |
| 打开尾链之后低优先级插进了高优先级 | 这不是尾链的定义；检查抢占级 | `#source-pm0056-nvic` | 尾链不改变谁有权抢占 |
| `__disable_irq()` 之后仍进了 NMI | 这是预期，不是 PRIMASK 失效 | `#source-pm0056-nvic` | PRIMASK 挡可配置优先级；NMI 除外 |
| PA0 已经占用 EXTI0，PB0 不再触发 | 换一个脚号 | `#source-rm0008-exti` | 同一编号的脚共用一条 EXTI 线 |
| F1 上 EXTI 不进中断 | 打开 AFIO 时钟再写 EXTICR | `#source-rm0008-exti` | 这句只在 F1 成立 |

机械抖动和 `volatile` 留在动手实验或核心原理里。10 ms 到 20 ms 的消抖没有钉在 PM0056 或 RM0008 上，不写进出处卡。

### 短 GIF

辅图 `assets/gif/nvic-preempt.gif`。内容是 NVIC 抢占的短循环：TIM2 正在执行，EXTI0 以更高抢占打断，然后返回。帧数不少于 3、不多于 12。它不画出「同抢占被挡住」的失败；那个失败只在静态主图上，免得关了动画就看不见。不替换 `nvic-interrupt-flow.svg`。

## 第 06 章写什么

订货号仍是 STM32F103C8T6，LQFP48。USART1 在 APB2，内核时钟 72 MHz 时 PCLK2 是 72 MHz，外设基址 `0x40013800`（第 22 章已经这么写）。默认脚是 PA9 = USART1_TX = 第 30 脚，PA10 = USART1_RX = 第 31 脚，来自 DS5319 Rev 20 图 8。复位后不是 PB6/PB7；重映射要另开 AFIO，不把重映射脚画进主图的正常路径。

### 原理与边界

- **16 倍过采样。** 这颗料的接收器用 16 倍波特率时钟采样。1 位停止位在第 8、第 9、第 10 个采样点上表决。起始位的确认序列是第 3、5、7 点和第 8、9、10 点，写在 RM0008 27.3.3。数据位用中间那三个点。主图至少把停止位上的 8、9、10 画出来。
- **BRR。** 16 倍时 `USARTDIV = fPCLK / (16 × 波特率)`。72 MHz、115200：`72e6 / (16 × 115200) = 39.0625`，小数 `0.0625 × 16 = 1`，BRR = `0x271`，`72e6 / (16 × 39.0625) = 115200`，分频误差是 0。`USART_BRR` 偏移 `0x08`，低 4 位是小数。这格从附录 D 照抄。章内现有的表把 39.0625、`0x271` 和 0.16% 写在同一行，这一批改掉：72 MHz 那一行的误差是 0%。大约 0.16% 留在 36 MHz、BRR `0x138` 那一行，并写明那是 APB1 上的 USART2，不是这只 USART1。丢掉小数、只用尾数 39，也会得到大约 0.16%，但那不是写进 `0x271` 的结果。附录 A 已经指出这张表的问题；改完之后章和附录是同一笔账。不编辑附录 A 或附录 D。
- **8 倍过采样。** 在这颗 F103 上作废。`USART_CR1` 没有 OVER8。现有句子「F1/F4 支持 OVER8」改成：F103 只有 16 倍；8 倍要换到带 OVER8 的系列。F4 上 OVER8 选择 8 倍时，分母改为 `8 × 波特率`，小数位比 RM0008 的 4 位少一位，多出来的那一位保持清除。位号从冻结的 RM0090 抄进 `rm0090-usart-over8` 的 snapshot 和 scope。抄不到位号，就不追加这个 id，正文只保留「F103 上作废」，不编一个 8 倍的 BRR。旧坑表里「高频误码就去开 OVER8」在 F103 上不能当处理。
- **IDLE。** 115200、8N1 时一位约 8.68 µs，一帧 10 位约 86.8 µs。RM0008 里空闲线是一整帧的高电平。一次 IDLE 表示线已经空了大约一个帧时间，不表示对方协议里的长度字段到了。这句从附录 A 照抄。循环 DMA 的 `Size` 仍是写位置，不是这一次的增量，沿用罗盘，不改成增量。
- **帧错误。** 停止位在预期的采样点上不是高，硬件置 `USART_SR.FE`。无效数据仍然进 `USART_DR`。清除是先读 SR 再读 DR。只读 DR 清不掉。中断是否到来还要看 RXNE 或 CR3 的 EIE；单字节通信时 FE 本身不单独成为唯一的中断源。这句不要写成「FE 一定进中断服务」。

### 关键插图

主图文件 `assets/diagrams/sample-06-uart-frame.svg`，同样由 `gen_sample_figures.py` 生成，用 `_credit()`，不调用 `Svg.footer()`。

图上是一帧，字节用现有 `uart-bits.gif` 已经在用的 `0xA5`（LSB 先发：起始位 0，数据 1 0 1 0 0 1 0 1，停止位 1），这样辅图和主图说的是同一帧。标出：

- 脚位：LQFP48 第 30 脚 PA9 = USART1_TX，第 31 脚 PA10 = USART1_RX。空闲为高。
- 时间：一位约 8.68 µs，10 位约 86.8 µs。BRR `0x271`，16 倍，误差 0。寄存器偏移 `USART_SR 0x00`、`USART_DR 0x04`、`USART_BRR 0x08`、`USART_CR1 0x0C`。
- **正常路径。** 停止位为高。第 8、9、10 个采样点表决为 1，FE 不置位。
- **失败路径。** 停止位处这三点采到 0，FE 置位，数据仍在 DR。图上写出清除顺序：读 SR，再读 DR。
- **作废标注。** 「OVER8 / 8 倍」放在旁注，不占帧错误那条路径。旁注写明这颗 F103 的 CR1 位 31:14 保留，没有这个位。不在这张图上算 8 倍的 BRR。

图注写「自绘」，带 DS5319 Rev 20 图 8 和 RM0008 Rev 21 第 27 章。替代文本写出结论：停止位采到 0 就是帧错误，`0x271` 在 72 MHz、16 倍下误差是 0。不写「示意图」。

`uart-frame.svg` 和 `uart-bits.gif` 留在原节，标成辅图。关键插图写明：PDF 不播放 GIF 时，起始位、停止位、三个采样点和 FE 路径都在静态主图上。

### 时序或状态

一张表覆盖这一帧的位序和两个采样结果。列至少有：空闲（高）、起始位、`0xA5` 的 8 个数据位（LSB 先）、停止位。采样列写第 8、9、10 点。正常行停止位为 1，FE 为 0。失败行停止位三点为 0，FE 为 1，清除是读 SR 再读 DR。时间列用 8.68 µs 和 86.8 µs。BRR 列用 `0x271` 和误差 0，并有一行 36 MHz / `0x138` / 约 0.16%，标明 USART2 与 APB1。不把 0.16% 放回 `0x271` 那一格。

IDLE 行：线在停止位之后保持高，满一个帧时间（约 86.8 µs）才表示空闲，不是协议帧结束。

### 坑与出处卡

至少这些行：

| 现象 | 处理方向 | 链接 | 允许的主张 |
| --- | --- | --- | --- |
| 表上 USART1 的 `0x271` 被说成已经偏了 0.16% | 72 MHz、16 倍、带上小数位，误差是 0 | `#source-rm0008-usart` | `0x271` 的分频结果是 115200。0.16% 不是这一格 |
| 停止位错了仍读到一个字节，接着卡死 | 先读 SR 再读 DR 清 FE | `#source-rm0008-usart` | FE 置位时数据仍进 DR；只读 DR 不清标志 |
| 把 IDLE 当成对方一包已经结束 | 用长度或协议，不用 86.8 µs 当帧界 | `#source-rm0008-usart` | IDLE 是线路空闲满一个帧时间 |
| F103 上打开 OVER8 来修高频误码 | 这颗料没有该位；先核对 72 MHz 和 `0x271` | `#source-rm0008-usart` | CR1 位 31:14 保留 |
| 循环 DMA 把 `Size` 当成这一次新增的字节数 | 自己保存上次位置再相减，注意绕回 | `#source-stm32cube-f4` | 只支持 v1.28.3 那个例程里 `Size` 是写位置。不是 F103 的引脚证明 |
| 应用一次把 DMA 缓冲区当完整线性帧读完 | 读到 DMA 写位置为止 | `#source-majerle-uart` | 改写后的环位置边界。不支持新的波特率或脚位 |
| 半传输和 IDLE 好像总会成对出现 | 不把帖子里的时序写成手册数字；空闲长度仍用 86.8 µs 那一格 | `#source-st-uart-idle` | 经验线索，未升格为规范。不支持新的寄存器值 |

若冻结的 Cube 例程自己写出 HT 与 IDLE 可以相邻触发，再追加一行，主张限于该例程，链接 `#source-stm32cube-f4`。读不到这个行为，就不追加这一行。论坛那一行无论哪种结果都保留，而且只作为线索。

### 短 GIF

辅图 `assets/gif/uart-idle.gif`。内容是空闲检测：一帧结束后 RX 保持高，满一个帧时间后标出 IDLE 和 86.8 µs。帧错误的三点采样只放在静态主图上。帧数不少于 3、不多于 12。不替换 `uart-bits.gif`，也不把逐位发送再做一遍。

## 插图标准

沿用上一份设计里的逼真、翔实、生动、可印刷、自绘。这一批把「主图」和「短 GIF」拆开，避免 GIF 把主图换掉。

静态主图：

- 用 `tools/svgkit.py`，生成脚本是 `tools/gen_sample_figures.py`。两章各一张，中英引用同一文件。中文路径 `../assets/diagrams/...`，英文路径 `../../assets/diagrams/...`。
- 不调用 `Svg.footer()`。落款用脚本里已有的 `_credit()`：左侧是文档号，右侧是「自绘 · 静态 · CC BY 4.0」。
- 没有 `<animate`、`@keyframes`、`animation:`。图上同时有正常路径和失败路径。
- 替代文本写结论。图注写「自绘」，不写「实拍」「手册截图」「矢量动画」。
- 单张小于 60 KB。放不下就拆成主图加局部，每张仍争取小于 60 KB。拆开仍超过时，在实施 PR 里写出字节数和原因，不把图画回简笔，也不把 60 KB 改成仓库新默认值。
- 登记进 `assets/README.md` 第四节，和 `sample-00-boot-state.svg`、`sample-03-gpio-led.svg` 并列。

短 GIF：

- 必做的两条走 `tools/gen_gifs.py`，加入 `BUILDERS`，这样 `tools/check_assets.py` 能逐像素对上重新生成的帧。`minigfx.py` 只有 5×7 英文点阵，GIF 上的字用 ASCII。
- 每条少于 500 KB，帧数见上面两节。两章都引用自己的那条 GIF，图注写明它是网页和公众号辅图，印刷以静态主图为准。
- `gen_gifs.chrome()` 自带的页脚可以留在 GIF 里。那条页脚不是静态主图的 `Svg.footer()`。
- 不改已有 6 个 BUILDERS 的像素。不重跑它们来「顺便」换画面。
- `tools/svg2gif.py` 依赖写死的 Windows Chrome 路径，这一批不把它当成必经步骤，也不为了它去改 CI。已有的 `*-zh.gif` 不重做。若另外导出一张公众号 GIF，它只能来自非主图的动画 SVG，而且不能成为章内唯一的关键插图。

PDF 关掉动画之后，读者只看静态主图和图注，就能指出失败发生在哪一段。第 04 章是「同抢占不能嵌套」。第 06 章是「停止位第 8、9、10 点为 0，FE 置位」。

## 工作流与 PR 节奏

### 本 PR（设计）

只新增本文件。不改 `docs/04`、`docs/06`、`docs/en/`、`stm32-book/`、`CREDITS.md`、`assets/`、`tools/`。不升版本，不打 tag，不发 Release。

### 实施 PR（下一轮，不在本 PR）

顺序固定：

1. **核对扫描。** 写出 `2026-10-25-batch2-04-06-lock.json`。章号保持 04 和 06。
2. **许可门。** 写出 `2026-10-25-batch2-04-06-source-list.json`。先有清单，再改正文。
3. **静态主图和短 GIF。** 先提交 SVG、GIF 和生成脚本，再写正文。主图不依赖 GIF。
4. **中英加厚。** 四份 Markdown 一起提交。
5. **登记。** 新来源追加进两份 manifest。更新这两章罗盘的来源数组。`CREDITS.md` 第六节增加 v1.1.1 小节。`revisions.json` 在条目最前加上 1.1.1，日期用准备合并当天的 UTC 日期。两份 manifest 的 `version` 改为 `1.1.1`，`date` 用同一天。`stm32-book/README.md` 的当前版本句改为 **v1.1.1**。发布一节里的 tag 名改成 `v1.1.1`，并加上「不要把 1.1.0 的产物标成 1.1.1」。这一步仍不创建 tag，也不创建 Release。修订说明只写第 04 章和第 06 章加厚了什么，用文件名前缀，不写尚未做的章。
6. **测试。** 新增 `stm32-book/tests/test_batch2_chapters.py` 和 `stm32-book/tests/test_batch2_sources.py`，照着样本测试检查四块、共享数字、主图禁词和许可门。不放宽 `test_sample_chapters.py` 对 00 与 03 的断言。`test_build.py` 里当前版本从 `1.1.0` 改为 `1.1.1`，历史列表保留 `1.1.0` 以及 1.0.8 到 1.0.0。不删 `0x271`、`167 ns`、账本名和出版书签长度为 44 的断言。
7. **CI 变绿之后停下来等人复审。** 复审对象是构建出的中英 HTML 里的这两章。人接受之前不合入，也不开下一批章。

实施 PR 的 diff 可以碰这两章中英正文、两份 manifest 的新 `sources` 和这两章罗盘、新图与生成脚本、`assets/README.md`、`CREDITS.md`、版本与修订、新的锁定文件和来源清单、新测试，以及 `test_build.py` 里的版本字符串。不碰其余章的正文，不改 `build_html.py`。

## 验收

### 本设计 PR

- 新增文件只有 `docs/superpowers/specs/2026-10-25-classic-encyclopedia-batch2-04-06-design.md`。
- 章节、`stm32-book/`、资产、工具和 `CREDITS.md` 与基线 `e8afafc` 相同。
- 没有新的 SVG 或 GIF，版本号仍是 1.1.0。

### 实施 PR

- 中文两章各有且仅有一次：`## 原理与边界`、`## 关键插图`、`## 时序或状态`、`## 坑与出处卡`。英文对应四个标题同样各一次。
- 两章都不再有 `## ⚠️ 常见坑与排查` 或 `## ⚠️ Pitfalls and troubleshooting`。
- 每章关键插图的第一张图是对应的静态 SVG。图上能看出正常路径和失败路径。GIF 不是这一节唯一的图。
- 中英都有这些数字，而且彼此一致：第 04 章的 8 个寄存器名、`167 ns`、`NVIC_PRIORITYGROUP_4`、`PRIMASK`、`NMI`、`EXTI0`、`TIM2`；第 06 章的 `STM32F103C8T6`、`PA9`、`PA10`、`30`、`31`、`0xA5`、`0x271`、`39.0625`、`8.68`、`86.8`、`0x138`、采样点 8、9、10、`FE`。第 06 章里 `0x271` 所在的误差格是 0，不是 0.16%。第 06 章的坑卡含 `#source-majerle-uart`、`#source-st-uart-idle`、`#source-stm32cube-f4`、`#source-rm0008-usart`。第 04 章的坑卡含 `#source-pm0056-nvic` 和 `#source-rm0008-exti`。
- 静态 SVG 小于 60 KB，不含动画标记，含「自绘」，不含「实拍」和「矢量动画」。两条新 GIF 小于 500 KB，并且在 `BUILDERS` 里。
- 新 `#source-` 都能在构建出的 HTML 里找到 `id="source-..."`。已有 `majerle-uart`、`st-uart-idle`、`stm32cube-f4`、`pm0056`、`rm0090` 的对象与基线逐字段相同。
- 附录 D 三套账和附录 A 的正文 diff 为空。`test_build.py` 对 `0x271` 和出版书签条数的断言仍在。
- 除 04 与 06 的中英四份以外，`docs/` 章节正文 diff 为空。第 01 章和第 02 章的图文件 diff 为空。
- 下面三条通过；改了生成脚本时再跑第四条：

```bash
python3 -m unittest discover stm32-book/tests -v
python3 stm32-book/build_html.py --check
python3 stm32-book/build_html.py --lang en --check
python3 tools/check_assets.py
```

- 没有 tag，没有 Release。章号显示仍是文件名前缀加 1。`build_html.py` 的 diff 为空。

## 未决问题

没有会挡住实施的未决项。下面几项按此处的默认执行，复审时可以改口，不需要再写一版设计才开工：

1. **社区中断例程。** 许可门若是空的，第 04 章只吸收 RM0008 与 PM0056。不临时换一份 GPL 仓库来凑署名。
2. **8 倍的位号。** 抄得到 RM0090 的 OVER8 位号才追加 `rm0090-usart-over8`。抄不到就只保留「F103 上没有 OVER8」，主图仍用 16 倍和 `0x271`。
3. **HT 与 IDLE 相邻。** 只有冻结的 Cube 例程写了这个行为，才做成出处卡；否则留在相关资源，不升级成规范数字。
4. **主图体积。** 先拆图。拆开仍超过 60 KB 时在实施 PR 里说明，不降低画法标准。
5. **图目录。** 这一批不加。

## 英文提要

Thicken only chapters 04 (interrupts and the NVIC) and 06 (UART), in Chinese and English, on top of v1.1.0 (`e8afafc`, PR #21). Use the same four sections as chapters 00 and 03. Each chapter gets one printable static SVG from `gen_sample_figures.py`, with a normal path and a failure path, and no `Svg.footer()`. Chapter 04 draws the eight-register exception stack at about 167 ns and the failure where equal preemption priority blocks nesting; NMI stays outside that mask. Chapter 06 draws one 8N1 frame of `0xA5` on PA9/PA10 (LQFP48 pins 30 and 31), samples 8/9/10, BRR `0x271` with zero divider error at 72 MHz and 16×, and the framing-error path. The existing 0.16% figure stays on the 36 MHz `0x138` row. OVER8 is void on STM32F103C8T6 because RM0008 leaves USART_CR1 bits 31:14 reserved. One short GIF per chapter is auxiliary only. Register new sources by appending ids. Rewrite the MIT MaJerle note into a pitfall card; keep the ST community UART thread as an index. Bump the book to 1.1.1 during implementation, do not tag or release, and stop for human review before squash-merge. This design PR only adds this file.

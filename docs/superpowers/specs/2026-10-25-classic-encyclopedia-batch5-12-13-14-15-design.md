# 第 12、13、14、15 章加厚设计

日期：2026-10-25  
状态：待人审。人接受这份规格之前不实施  
基线：`main` 上的整书 **v1.2.9**（`adc5cd7ae2314195f5214a48ffdfc53e69f76851`，PR #53，2026-10-25）  
上一份设计：[2026-10-25-book-posters-align-design.md](2026-10-25-book-posters-align-design.md)（PR #51）。四块模板来自 [2026-10-25-classic-encyclopedia-thicken-design.md](2026-10-25-classic-encyclopedia-thicken-design.md)（PR #18）。上一批加厚是 [2026-10-25-classic-encyclopedia-batch4-01-07-10-11-design.md](2026-10-25-classic-encyclopedia-batch4-01-07-10-11-design.md)。密度刀 F 是 [2026-10-25-book-density-F-design.md](2026-10-25-book-density-F-design.md)，已经在 1.2.8 收过空白。  
本文件只记录这一批的设计。它不改章节正文，不画新图，不改 `stm32-book/` 构建，不升版本号，不打 tag，不发布 Release，不写实施计划。

章号按文件名前缀锁死，不按主题改名。文件 `12` 是 Flash 与 IAP，文件 `13` 是 bxCAN，文件 `14` 是 USB 设备，文件 `15` 是 FreeRTOS 入门。不要把这一批写成第 28 章的 RTOS 生态，也不要写成低功耗、调试或网络。

## 背景

v1.2.9 已经按大典四块加厚的是第 00、01、02、03、04、05、06、07、08、09、10、11 章。海报对齐只重画了 29 张讲解海报，没有加厚正文。这一批只加厚另外四章，中文和英文一起写：

| 文件前缀 | 中文 | 英文 | 这一章在讲 |
| --- | --- | --- | --- |
| `12` | `docs/12-Flash与IAP升级.md` | `docs/en/12-flash-iap.md` | 页、半字、Boot/APP 划分、跳转 |
| `13` | `docs/13-CAN总线.md` | `docs/en/13-can.md` | 位时间、重映射、终端、总线关闭 |
| `14` | `docs/14-USB.md` | `docs/en/14-usb.md` | 48 MHz、D+/D−、描述符长度 |
| `15` | `docs/15-FreeRTOS入门.md` | `docs/en/15-freertos.md` | 节拍、字栈、FromISR 优先级 |

读者看到的章号仍是文件名前缀加 1：文件 `12` 在书里是第 13 章，`13` 是第 14 章，`14` 是第 15 章，`15` 是第 16 章。源文件的一级标题继续带 `12`、`13`、`14`、`15`。这一批不改这个加 1。

第 01 章已经钉过两字：第 0 字是 MSP，第 1 字是 `Reset_Handler`，IRQ 入口是 `VTOR + 4×(IRQn + 16)`。第 02 章已经钉过 HSE 在第 5 脚 PD0、第 6 脚 PD1，以及 `USBPRE=0` 时 72 MHz ÷1.5 = 48 MHz。第 04 章已经钉过硬件入栈约 167 ns，以及 HAL 默认 `NVIC_PRIORITYGROUP_4`、数值越小越优先。第 06 章已经钉过 USART1 在第 30 脚 PA9、第 31 脚 PA10。第 07 章已经把第 45 脚 PB8、第 46 脚 PB9 留成 I2C1 重映射，不画进 I2C 的正常路径。这几张图都不重画。167 ns 不进第 15 章的四块。

对照 v1.2.9 核对过的事实：

1. **这四章还没有四块。** 已经加厚的章在 `<!-- /video: -->` 之后、学习目标之前，有 `## 原理与边界`、`## 关键插图`、`## 时序或状态`、`## 坑与出处卡`（英文是 `Principle and boundary`、`Key figures`、`Timing or state`、`Pitfalls and source cards`）。这四章仍从学习目标写起。中文坑还在 `## ⚠️ 常见坑与排查`，英文坑还在 `## ⚠️ Pitfalls and troubleshooting`，坑表没有 `#source-`。
2. **第 12 章把这颗 C8 注成了小容量，地图本身已经是 64 KB。** 罗盘边界写：F103 中容量按 1 KB 页擦除、按半字编程；解锁先写 KEY1 `0x45670123`，再写 KEY2 `0xCDEF89AB`；大容量才是 2 KB/页。正文代码注释却写「F103C8 小容量 1KB/页」。STM32F103C8T6 是中容量，闪存 64 KB。小容量也是 1 KB/页，但不是这颗料的密度名。页大小 1024 保留，密度名改成中容量。本章地图：Bootloader `0x08000000` 起 16 KB，参数区 `0x08004000` 起 2 KB，APP `0x08004800` 起 46 KB。`16 + 2 + 46 = 64`。`0x08004800 + 0xB800 = 0x08010000`。`examples/iap-bootloader` 把 APP 长度写成 `0xB800`。C8 最后一页从 `0x0800FC00` 起，这一页落在 APP 区里面，不是 Bootloader 外面的空页。`0x0801FC00` 是 128 KB 料的最后一页，在这颗 C8 上越界。F1 编程粒度是半字。按字节编程是 F4 的句子，在 C8 上作废。选项字节的 `0xA5` 已经在第 01 章和 `pm0075-rdp`。F4 的 `0xAA` / `0xCC` 在这颗料上作废。本章不重开那把钥匙。
3. **第 13 章的 500 kbit/s 已经在罗盘，推荐脚和「没有 PD0/PD1」互相打架。** 罗盘：APB1 为 36 MHz 时，预分频 9、BS1 为 5、BS2 为 2，一共 8 个时间份额，采样点 75%，`36e6 / (9 × 8) = 500` kbit/s。10 个时间份额要预分频 7.2；写成 8 得到 `36e6 / (8 × 10) = 450` kbit/s。发送错误计数到 256 进入总线关闭。一个时间份额是 `9 / 36e6 = 250` ns，一个位是 2 µs，采样落在第 6 个时间份额，也就是 1.5 µs。`examples/can-bxcan` 用的就是预分频 9 这一行，标准 ID 放进 `FilterIdHigh` 时左移 5 位，ABOM 打开时硬件自己数完 128 次、每次 11 个隐性位。复位默认 CAN1 在 PA11/PA12，和 USB 是同一对脚。BluePill 的工作点是第一种重映射：PB8 收、PB9 发。正文却写「C8 没有 PD0、PD1」。第 02 章已经把 LQFP48 第 5 脚钉成 PD0-OSC_IN、第 6 脚钉成 PD1-OSC_OUT。这两只脚在，它们接着 8 MHz 晶振。CAN 重映射到这两只脚会拆掉 HSE，不是「封装没有」。例程 README 里那句「48 脚封装没有」这一批不改例程，章节正文不得再抄。硬件表把 BluePill 的 CAN1 写成 PA11/PA12，和开篇的 PB8/PB9 不是同一条正常路径。接线节改成重映射这一对；PA11/PA12 留在失败路径。两端各 120 Ω 是例程里的接法。两只 120 Ω 并联的直流负载是 60 Ω。正文「差分阻抗约 60 Ω」把负载写成了电缆特性阻抗，这句改正，不把 60 Ω 升格成电缆规范。
4. **第 14 章的描述符账已经在罗盘和附录 D，主图仍是枚举动画。** 附录 D「USB 67 字节」和罗盘同一笔描述符账：PLL 72 MHz 且 `USBPRE = 0` 时 `72 / 1.5 = 48` MHz。`examples/usb-cdc` 的设备描述符第 1 字节是 `0x12`，共 18 字节；`bMaxPacketSize0` 是 `0x40`，即 64。VID/PID 是 `0x1209/0x0001`，不是 ST 例程常见的 `0x0483/0x5740`。配置集合 `wTotalLength` 是 `0x0043`，即 67。`bMaxPower` 的 `0x32` 是 100 mA。全速批量和中断的包上限都是 64 字节；1023 只属于全速等时。例程里的通知端点是 8 字节，批量端点是 64 字节。`USBPRE = 1` 时 USB 时钟是 72 MHz，不是 48 MHz，这句和第 02 章同一笔。脚位和上拉只在罗盘里，不在附录 D 那一行：PA11 是 DM，PA12 是 DP，全速在 D+ 上拉 1.5 kΩ。F103 的 USB 是设备，不是主机，也不是 480 Mbit/s。`USB_LP_CAN1_RX0` 与 bxCAN 接收是同一条中断。第 31 脚已经是 PA10，第 34 脚已经是 PA13，中间两只默认是第 32 脚 PA11、第 33 脚 PA12。把 1.5 kΩ 接到 DM 上，主机不会把它认成这颗全速设备。
5. **第 15 章的字栈和 `0x50` 已经在罗盘，时基仍写成笼统的 TIMx。** 罗盘：FreeRTOS 要求分组 `GROUP_4`。4 位优先级时 `5 << (8 − 4) = 0x50`，能调用 FromISR 的中断优先级数值要大于等于 5。NVIC 数值 0 是最高优先级，调用这些 API 会停在 `configASSERT`。任务优先级的方向相反。`xTaskCreate` 的栈深度单位是字。`examples/freertos-task` 里 LED 是 128 字，等于 512 字节；KEY 是 192 字，等于 768 字节；UART 是 256 字，等于 1024 字节。LED 和 UART 的任务优先级是 1，KEY 是 2。`EXTI0` 的抢占优先级写成 5。`configTICK_RATE_HZ` 默认 1000，一个 tick 是 1 ms。先干 3 ms 再 `vTaskDelay(10)`，周期接近 13 ms；`vTaskDelayUntil` 的 10 ms 仍是 10 ms。例程 README 把 HAL 时基定在 TIM4，不是 SysTick。正文只写「改成 TIMx」。STM32F103C8T6 是 Cortex-M3，没有 FPU。坑表里「选带 FPU 的移植」在这颗料上作废。第 28 章的 17.2% 预算不进这一章。
6. **许可门与已有 id 保持原样。** 允许吸收的仍是 ST 手册里的事实（自己的话重写），以及 MIT、BSD-2-Clause、BSD-3-Clause、ISC、CC BY 4.0、CC BY 3.0、CC0。GPL、LGPL、CC BY-NC、CC BY-ND、Apache-2.0、保留所有权利、未写许可的材料只留链接。USB-IF 规范、ISO 11898、TJA1050 与 SN65HVD230 的厂商手册、pid.codes 的站点政策、FreeRTOS 网站正文，都不吸收句子。`usb20` 和 `freertos-priority` 保持「仅链接」。`sources` 只追加。已有 id 一个字段都不改。
7. **全 29 章最终都要加厚。** 本批只规格化文件 `12`、`13`、`14`、`15`。再下一批仍是 4 章，章号到那时再锁。本文件不预选文件 `16` 或 `28`。密度刀 F 已经收过阅读面空白。这一批只加内容的密度，不加另一刀 CSS。

## 目标与非目标

### 目标

- 只把第 12、13、14、15 章加厚到和第 00 到第 11 章相同的四块密度。中文和英文一起写完。
- 每章一张可印刷的静态主图：正常路径和失败路径都在图上，封装脚位、地址、阻值和时间是真的。另加一条短 GIF，只做网页和公众号辅图。
- 数字钉在已经冻结的 RM0008 Rev 21、DS5319 Rev 20、PM0075、PM0056，以及这四章罗盘和附录 D 已有的格子上。第 12 章的密度名改成中容量，页大小仍是 1 KB。第 13 章的 500 kbit/s 跟罗盘同一笔账，工作脚是第 45 脚和第 46 脚。第 14 章的 48 MHz 和 67 字节跟罗盘、附录 D 同一笔账。第 15 章的 128 字和 `0x50` 跟罗盘同一笔账。罗盘只写「别的定时器」；HAL 时基按例程 README 写明是 TIM4。
- 新出处追加进两份 manifest 的 `sources`。章内坑卡使用 `#source-...`。`CREDITS.md` 第六节记下这一批改写吸收了什么。
- 实施合入时把整书从 1.2.9 升到 **1.3.0 · 2026-10-25**。中英文共用这个版本号和这个日期。这一批不打 tag，不创建 Release。
- 实施 PR 在 Book CI 变绿之后停下来等人复审。人接受之前不合入。Book CI 变绿不等于自动 squash 合入。

### 非目标

- 不加厚除 12、13、14、15 以外的任何章。已经加厚的 00 到 11 保持原样。文件 `16` 的低功耗、文件 `17` 的调试、文件 `28` 的 RTOS 生态不进本批。不把 17.2%、167 ns、21 µs 写进这四章的四块。
- 不重画 `sample-00-boot-state.svg`、`sample-01-swd-vectors.svg`、`sample-02-clock-tree.svg`、`sample-04-exception-stack.svg`、`sample-06-uart-frame.svg`、`sample-07-i2c-addr.svg`。第 12 章只用旁注指向第 01 章的两字和 `0xA5`。第 13 章不把第 07 章的 I2C 开漏画成同时有效。第 14 章不重画第 02 章的时钟树。第 15 章不重画第 04 章的入栈。
- 不改密度刀 F 的令牌、`book.css` 和间距。不把样式、字号、行长或页边再收一刀。不改 `stm32-book/build_html.py`。
- 不重画 29 张讲解海报，不改 `assets/video/` 里的 png、mp4、srt，不改 `tools/gen_narrated.py`。`<!-- video: -->` 与 `<!-- /video: -->` 之间的旁白保持原样，包括第 13 章旁白里那句「C8 没有那两只脚」。旁白不重录。视频块以外的正文不得再写这句。
- 不重选样本，不改 `docs/superpowers/plans/` 里已有的锁定文件和来源清单。不改 `tools/scan_sample_chapters.py`。本设计 PR 不新增实施计划。
- 不改总纲、Batch2、Batch3、Batch4 规格、观感规格、海报规格、密度规格、CONTENT_GUIDE 规格，也不改两份 `CONTENT_GUIDE.md`。
- 不实现 v1.2.9 或 v1.3.0 的 GitHub Release，也不打 `v1.2.9` 或 `v1.3.0` 的 tag。
- 出版书签仍是现在的 44 条。不把新的二级标题收进书签。
- 不改附录 A 的既有契约，不改附录 D 已有各行的算术，不手改 `stm32-book/book/E-参考资料.md` 或英文对应文件。附录 E 的卡片仍由 `sources` 生成。不把 500 kbit/s 或 IAP 地图新写成附录 D 的一行。
- 不替换、不重画已有图。第 12 章留下 `flash-iap.svg`。第 13 章留下 `can-arbitration.svg`。第 14 章留下 `usb-enumeration.svg`。第 15 章留下 `freertos-scheduler.svg`。新主图是加进去的。
- 不把厂商手册、USB-IF 原文、ISO 原文、官方插图或社区原文放进仓库。
- 不加图目录或表目录，不加第 30 章，不改 `docs/00`–`28` 的文件名。
- 不新开可烧录工程。不改 `examples/iap-bootloader/`、`examples/can-bxcan/`、`examples/usb-cdc/`、`examples/usb-hid/`、`examples/freertos-task/`。例程里「小容量」和「48 脚封装没有」这两句留在例程，章节用正确的说法，不回头改例程。

## 来源与许可

四层用法和总纲、Batch4 相同。

允许写进正文的，仍按这个顺序：

1. ST 的 RM、DS、PM：只吸收事实，用自己的话写，附文档号和可点击的入口。不粘贴段落，不描官方图。
2. MIT、BSD-2-Clause、BSD-3-Clause、ISC、CC BY 4.0、CC BY 3.0、CC0：可以改写教学要点。许可证不强制署名时，本书仍署名。FreeRTOS 内核是 MIT。本仓库例程是 MIT。
3. 其他许可证：只留链接。含 GPL、LGPL、CC BY-NC、CC BY-ND、Apache-2.0、保留所有权利、未写许可的帖子和视频。USB-IF、ISO、收发器厂商手册、pid.codes 站点政策和 FreeRTOS 网站正文都在这一层。

权威数字以第 1 层、罗盘边界和附录 D 已有格子为准。社区材料只支持「这个坑有人踩过」。帖子里的寄存器值，要在 RM/DS/PM 或本仓库例程上重新钉住之后才能进「原理与边界」或「时序或状态」。钉不住的，出处卡的主张写成「经验线索，未升格为规范」，并且这一行不引入新的寄存器值。

TJA1050 的 5 V 和 SN65HVD230 的 3.3 V 留在硬件节，标明那是模块的供电，不进出处卡，不进主图的规范主张。YMODEM 的 128 字节和 1024 字节留在核心原理。没有一份许可允许吸收的协议文本时，这两个长度不进出处卡。

### 追加的来源 id

新 id 只追加在两份 `sources` 对象的末尾。已有 id 的标题、URL、snapshot、许可、scope 都不改。中英两份的 `url`、`snapshot`、`license`、`accessed` 用同一串字符；`title`、`authority`、`scope` 用对应语言。`accessed` 用 `2026-10-25`。章罗盘的 `sources` 数组在原有 id 之后追加新 id，不删除已有 id。

RM0008 的 PDF 与已有 `rm0008-rcc` 相同。DS5319 的 PDF 与已有 `ds5319-clock` 相同。不另找一份修订。

| 新 id | 冻结点 | 用在 | 不复制 |
| --- | --- | --- | --- |
| `rm0008-flash` | RM0008 Rev 21 第 3 章。中容量按 1 KB 页擦除，编程粒度是半字。解锁向 `FLASH_KEYR` 先写 `0x45670123`，再写 `0xCDEF89AB`。大容量的 2 KB/页在 C8 上作废。擦掉的半字读回 `0xFFFF`。编程只能把 1 写成 0。章号若印出的标题不是嵌入式闪存，改用印出的章号，主张不变 | 第 12 章的页、半字和两把钥匙 | 不重写第 02 章的等待周期。不把 `0xAA` 写成这颗料的无保护键。不粘贴编程时序图 |
| `rm0008-can` | RM0008 Rev 21。默认先对第 21 章 bxCAN。位时间由同步段 1 个时间份额加 BS1 加 BS2。`CAN_BTR` 的预分频字段以印出的位为准。发送错误计数到 256 进入总线关闭。恢复要看到 128 次、每次 11 个连续隐性位。过滤器组是 14 个，接收 FIFO 是 2 个。32 位过滤器里标准 ID 占印出的那些位；本仓库例程把它放进 `FilterIdHigh` 并左移 5。重映射字段以印出的编码为准：一种到 PB8/PB9，一种到 PD0/PD1。章号或位域和这里不同时，用印出的，500 kbit/s 仍是预分频 9 与 8 个时间份额 | 第 13 章的位时间、总线关闭和过滤器位移 | 不编 CAN 基址。不吸收 ISO 11898。不把 450 kbit/s 写成工作点。不改 `rm0090` |
| `ds5319-usbcan` | DS5319 Rev 20 表 5 的 LQFP48 列。第 31 脚已经是 PA10，第 34 脚已经是 PA13。中间默认第 32 脚 PA11、第 33 脚 PA12。PA11 的复用含 USB_DM 和 CAN_RX，PA12 的复用含 USB_DP 和 CAN_TX。第 45 脚 PB8、第 46 脚 PB9 的重映射含 CAN。第 5 脚和第 6 脚就是已有 `ds5319-clock` 的 PD0、PD1，封装上有这两只脚。印出的脚号不同就改脚号，信号名仍按印出的复用列 | 第 13 章和第 14 章的脚。同一对 PA11/PA12 不能同时当 CAN 和 USB | 不改 `ds5319-clock`、`ds5319-i2c`、`ds5319-gpio`。不描图。不编收发器的管脚 |
| `rm0008-usb` | RM0008 Rev 21。默认先对第 23 章 USB device。F103 这一块是全速设备，不是主机。USB 时钟要 48 MHz。与 bxCAN 接收共用的中断名以印出的向量名为准，默认先写 `USB_LP_CAN1_RX0`。片内 D+ 上拉只有手册印出了才写入 snapshot，并写上印出的阻值。没印出阻值就不编一个千欧。章号或向量名不同时用印出的，48 MHz 的主张不变 | 第 14 章的设备边界和共享中断。第 13 章只交叉引用这一条中断，不另开 id | 不粘贴 USB-IF 第 9 章。不把 480 Mbit/s 写进这颗料。不改 `usb20`。不改 `rm0008-rcc` 里的 `USBPRE` |
| `freertos-syscall` | FreeRTOS Kernel V11.3.2，与已有 `freertos-1132` 同一份发行标签。MIT。Cortex-M 端口把库优先级左移 `(8 − 优先级位数)` 后写入 `BASEPRI` 用的那个常数。4 位优先级、库优先级 5 时，移完是 `0x50`。数值更小的中断不得调用 FromISR。任务优先级数值更大的先跑。`xTaskCreate` 的深度单位是字。heap_4 会合并相邻空闲块。互斥量有优先级继承，二值信号量没有。若这份标签里的演示工程印出的库优先级不是 5，snapshot 改记印出的公式，本仓库例程的 EXTI 仍是 5 | 第 15 章的 `0x50`、字栈方向和互斥量。不覆盖第 28 章 | 不改 `freertos-1132` 和 `freertos-priority`。不粘贴 `heap_4.c`。不吸收网站正文。不把 17.2% 写进来 |

来源清单的 `absorb` 必须含上表五个 id。没有条件追加的第六个 id。片内上拉的阻值若印在 RM0008 或 DS5319 里，写进已有的新 id snapshot，不为此再开一个 id。

`freertos-syscall` 的 URL 用 `https://github.com/FreeRTOS/FreeRTOS-Kernel/releases/tag/V11.3.2`。许可字符串写 `MIT`。

许可门若找不到新的 MIT、BSD 或 CC BY/CC0 社区例程，来源清单里的社区列表就是空的。空列表不挡住加厚。例程主张走已有的 `project-examples`，不新开例程 id。不吸收未写许可的博客，不吸收 GPL 的 libopencm3，不吸收 Apache-2.0 的 RT-Thread，不吸收 USB-IF 和 ISO 的句子，不吸收收发器厂商手册。

### 沿用、但不改写对象的 id

| 已有 id | 这一批怎么用 |
| --- | --- |
| `pm0075-rdp` | 第 12 章交叉引用：无保护是 `0xA5`，编程回 `0xA5` 会先整片擦除主闪存。不在这一章展开第 11 章的喂狗。不改这条对象 |
| `pm0056-vector` | 第 12 章交叉引用：第 0 字是 MSP，第 1 字是复位。APP 的 `VTOR` 指到 `0x08004800`。不改这条对象 |
| `ds5319-swd` | 只交叉引用已经写上的 64 KB 闪存。最后一页的算法用这 64 KB，不改这条对象 |
| `ds5319-clock` | 第 13 章交叉引用：第 5 脚 PD0、第 6 脚 PD1 是晶振脚，封装上有。不改这条对象 |
| `rm0008-rcc` | 第 14 章交叉引用：`USBPRE=0` 得到 48 MHz，`USBPRE=1` 得到 72 MHz。不改这条对象 |
| `ds5319-i2c` | 第 13 章交叉引用：第 45 脚 PB8、第 46 脚 PB9 也是 I2C1 重映射。两章的主图不把两种功能画成同时有效。不改这条对象 |
| `project-examples` | 第 12 章交叉引用 `0xB800`。第 13 章交叉引用预分频 9、左移 5、120 Ω 和 128×11。第 14 章交叉引用 18 字节、67 字节、`0x1209/0x0001`。第 15 章交叉引用 128/192/256 字、优先级 1 和 2、EXTI 优先级 5、TIM4。不改这条对象 |
| `rm0090` | 第 12 章和第 13 章只把 F4 的扇区、F4 的 bxCAN 留成「换系列才成立」。不改这条对象 |
| `usb20`、`freertos-priority`、`freertos-1132`、`an2606`、`an3965` | 不改。协议和网站正文继续只留链接。系统存储器 Bootloader 不画进第 12 章的用户闪存地图 |
| `pm0056`、`pm0056-nvic` | 不改。167 ns 不进第 15 章 |

出处卡的字段仍是现有附录 E 的一套：`title`、`authority`、`url`、`snapshot`、`accessed`、`license`、`scope`。`url` 必须是 `https://`。章内第四块每一行只有一个主张，并带一个 `#source-`。一行写清现象、原因、处理、链接、该来源允许支持的主张。

`CREDITS.md` 第六节现在收到第 01、07、10、11 章（v1.2.3）。这一批在该节下面加一个小节「第 12、13、14、15 章（v1.3.0）」，保留前面的表。新表只列作品名、许可证、用在哪、链接。不贴手册原文。同一文件顶部的静态框图从 18 张改为 22 张，光栅动画从 16 个改为 20 个。只有第 12 章拆出第二张 SVG 时，静态框图改为 23 张，并在实施 PR 里写明拆图原因。

## 锁定

章号按文件名前缀锁死：`12`、`13`、`14`、`15`。不再按「谁更薄」重选。不改成第 16 章或第 28 章，也不把已经加厚的章再开一遍。

实施开始时仍做一次核对扫描，只读这四章的中英八份。扫描确认两件事：四块标题还不存在；旧的「常见坑」标题还在。结果写到新文件 `docs/superpowers/plans/2026-10-25-batch5-12-13-14-15-lock.json`，带上运行时的 `git rev-parse HEAD`。不覆盖更早的锁定文件。若扫描发现四块已经有人写过，停下来，不叠第二套标题。

来源清单写到 `docs/superpowers/plans/2026-10-25-batch5-12-13-14-15-source-list.json`，字段沿用 Batch4 清单：`chapters` 是 `["12", "13", "14", "15"]`，`absorb` 里每一条有 `license_class`、`url`、`do_not_copy`、`points`。`license_class` 只允许 `ST-facts-restated`、`MIT`、`BSD-2-Clause`、`BSD-3-Clause`、`ISC`、`CC BY 4.0`、`CC BY 3.0`、`CC0`。许可字符串里不得出现 `GPL`、`LGPL`、`CC BY-NC`、`CC BY-ND`、`All rights reserved`。清单可以先于 manifest 提交；登记以 manifest 为准。

## 章节加厚模板

四块插在 `<!-- /video: -->` 之后、学习目标之前，和第 03 章相同。标题不加表情符号，中英各出现一次：

| 块 | 中文标题 | 英文标题 | 这一块要写完的事 |
| --- | --- | --- | --- |
| 1 | `## 原理与边界` | `## Principle and boundary` | 结论钉在哪颗订货号、哪路时钟、哪一版手册；换系列时哪一句作废 |
| 2 | `## 关键插图` | `## Key figures` | 静态主图在前，图注带关键数字和文档号。短 GIF 跟在后面，图注标明辅图 |
| 3 | `## 时序或状态` | `## Timing or state` | 一张能算回去的表。时间或状态迁移和主图是同一笔账 |
| 4 | `## 坑与出处卡` | `## Pitfalls and source cards` | 旧坑表里钉得住的行挪到这里。每行一个 `#source-` |

保留学习目标、硬件与接线、代码实现、动手实验、相关资源，以及英文的对应标题。保留 `## 🧠 核心原理` 和英文 `## 🧠 Core ideas`。和四块、罗盘或附录 D 冲突的数字，就地改成同一笔账，不保留两套说法。`## ⚠️ 常见坑与排查` 和英文 `## ⚠️ Pitfalls and troubleshooting` 删掉，不留空标题。

视频块、旁白和已有动画图留在原处。主图不放进 `<!-- video: -->` 块。代码仍按 `docs/CONTENT_GUIDE.md`：HAL，参数用宏。

中英的订货号、文档号、寄存器名、脚位和算式一致。英文可以更短，不能少一块，也不能少一个关键数字。

## 第 12 章写什么

订货号仍是 STM32F103C8T6，LQFP48。闪存跟第 01 章和第 02 章同一笔：64 KB，从 `0x08000000` 到 `0x08010000` 之前。中容量，1 KB 一页，一共 64 页。这一章的地图是本书和 `examples/iap-bootloader` 已经在用的那一版，不是手册规定的唯一划分。

### 原理与边界

- **中容量的页。** 擦除粒度是 1 KB。代码注释里的「小容量」改成中容量。大容量的 2 KB/页在这颗料上作废。页号从 0 到 63。第 63 页从 `0x0800FC00` 起。`0x0801FC00` 越出 64 KB，是主图的失败地址。
- **半字。** 编程地址按 2 字节对齐，一次写 16 位。擦掉之后读回 `0xFFFF`。已经写成 0 的位，不擦整页就变不回 1。按字节编程是 F4 的句子，在 C8 上作废。一个 32 位值要分两次半字写完。
- **两把钥匙。** 先写 `0x45670123`，再写 `0xCDEF89AB`，`CR.LOCK` 才清除。顺序反了，锁还在，擦除返回错误。这是主图的失败路径。写完上锁。
- **三块地图。** Bootloader：`0x08000000`，16 KB，16 页，到 `0x08004000` 之前。参数区：`0x08004000`，2 KB，2 页，到 `0x08004800` 之前。APP：`0x08004800`，46 KB，46 页，长度 `0xB800`，到 `0x08010000` 之前。三块相加是 64 KB。链接脚本的起始和 `SCB->VTOR` 都是 `0x08004800`。只改其中一个，跳进去的仍是 Bootloader 的向量。
- **两字。** APP 区第 0 字是 MSP，第 1 字在 `0x08004804`，是 `Reset_Handler`。跳转前读出这两字，写 MSP，写 `VTOR`，再跳。这跟第 01 章同一笔，不另画启动别名。`VTOR` 仍留在 0 是失败路径。
- **最后一页实验。** 没有 IAP 划分、程序又没有铺到末页时，`0x0800FC00` 可以拿来做擦写实验。地图一旦按上面三块使用，这一页属于 APP，不是参数区外面的空页。实验节写明这个差别。
- **读保护。** 无保护仍是 `0xA5`。解除会整片擦除主闪存。`0xAA` 和 `0xCC` 在这颗料上作废，只作为 F4 的对照出现在核心原理。不重画第 01 章。
- **这一章的 Bootloader 在用户闪存。** `BOOT1=0` 且 `BOOT0=1` 进的是系统存储器 `0x1FFFF000`，那是第 00 章和第 01 章的句子。不把它画成 `0x08000000` 上的 IAP。串口仍是第 06 章的第 30 脚 PA9、第 31 脚 PA10，图上只旁注，不重画那一帧。

F4 的扇区表留在核心原理，并写明换到 F407 才成立。参数区和 Bootloader 挤在同一个 16 KB 扇区里，是 F4 的失败，不占 C8 这张 1 KB 页的地图。页擦除的「约 20~40 ms」留在核心原理，标成数量级，不进四块，也不进 snapshot。

### 关键插图

主图文件 `assets/diagrams/sample-12-iap-map.svg`，由 `tools/gen_sample_figures.py` 追加一个函数生成，调用 `_credit()`，不调用 `Svg.footer()`。

图上是这 64 KB 和一次跳转：

- 地址：`0x08000000` 到 `0x08010000`。16 KB、2 KB、46 KB 三块，页高按 1 KB 标出第 0 页和第 63 页。第 63 页的地址是 `0x0800FC00`。
- **正常路径。** 先写 KEY1，再写 KEY2。半字写进 APP 区。然后从 `0x08004800` 读 MSP，从 `0x08004804` 读复位，`VTOR` 写成 `0x08004800`。
- **失败路径。** 钥匙顺序反了，`LOCK` 仍为 1。另一处把末页写成 `0x0801FC00`，落在 64 KB 外面。`VTOR` 留在 0 时，中断仍进 Bootloader。
- **旁注。** 按字节写在这颗料上作废。`0xA5` 只指向第 01 章，不把选项字节区画成第三张主图。不画 USART 帧。不画系统存储器 `0x1FFFF000`。

图注写「自绘」，带 RM0008 Rev 21 第 3 章和 PM0056 的两字。替代文本写出结论：这颗中容量是 1 KB 页；APP 从 `0x08004800` 起，长度 `0xB800`；跳转要装入第 0 字和第 1 字。不写「示意图」。

`flash-iap.svg` 留作辅图。关键插图写明：不播放它，页边界、两把钥匙和跳转用的两字都在静态主图上。

放不下 60 KB 时，把两字拆到 `assets/diagrams/sample-12-iap-vectors.svg`。第一张仍是地图。拆开的两张都用 `_credit()`，都不调用 `Svg.footer()`。只允许这个第二张文件名。

### 时序或状态

一张表用这 64 KB。列至少有：区、起始、长度、页数、结束于。必须有的行：Bootloader，`0x08000000`，16 KB，16 页，`0x08004000`；参数区，`0x08004000`，2 KB，2 页，`0x08004800`；APP，`0x08004800`，46 KB，46 页，`0x08010000`。末页行：`0x0800FC00` 是第 63 页，落在 APP 内。失败行：`0x0801FC00` 不在这 64 KB 里。钥匙行：先 `0x45670123`，后 `0xCDEF89AB`。半字行：地址 2 字节对齐，擦除态 `0xFFFF`。跳转行：`0x08004800` 的字是 MSP，`0x08004804` 的字是复位。

### 坑与出处卡

至少这些行：

| 现象 | 处理方向 | 链接 | 允许的主张 |
| --- | --- | --- | --- |
| 注释写成小容量，页大小却对 | 密度名改成中容量。页仍是 1 KB，共 64 页 | `#source-rm0008-flash` | 中容量按 1 KB 擦除。大容量的 2 KB/页在 C8 上作废 |
| 擦除返回错误 | 先写 KEY1，再写 KEY2。地址落在页边界上 | `#source-rm0008-flash` | 顺序是 `0x45670123` 然后 `0xCDEF89AB`。反序清不掉 LOCK |
| 写进去的字节读回来不对 | 按半字、按偶地址写。要改 0 回 1 先擦整页 | `#source-rm0008-flash` | 编程粒度是 16 位。擦除态是 `0xFFFF`。按字节编程在这颗料上作废 |
| 跳转后死机，或中断跑回 Bootloader | 从 `0x08004800` 装入 MSP 和复位，并写 `VTOR` | `#source-pm0056-vector` | 第 0 字是栈初值，第 1 字是复位。这一主张不新规定对齐位数 |
| APP 长度和链接脚本对不上 | 起始 `0x08004800`，长度 `0xB800` | `#source-project-examples` | `examples/iap-bootloader` 的 APP 是 46 KB，即 `0xB800` |
| 实验写到 `0x0801FC00` | C8 的最后一页是 `0x0800FC00` | `#source-ds5319-swd` | 这条来源已经写明 STM32F103x8 的闪存是 64 KB。128 KB 的末页在这颗料上作废 |
| 按 `0xAA` 解除读保护 | 这颗料的无保护是 `0xA5`，解除会整片擦除 | `#source-pm0075-rdp` | RDP 为 `0xA5` 才允许读出。编程回 `0xA5` 会先整片擦除 |

YMODEM、磨损均衡和 F4 扇区留在核心原理。F4 的 `0xAA` 若还出现，旁边写明在 STM32F103C8T6 上作废。

### 短 GIF

辅图 `assets/gif/iap-jump.gif`。内容是正常路径：两把钥匙按顺序写完，一个半字落进 `0x08004800` 之后，CPU 读出 MSP 和复位。帧数不少于 3、不多于 12。反序钥匙和 `0x0801FC00` 只放在静态主图上。不替换 `flash-iap.svg`。

## 第 13 章写什么

订货号仍是 STM32F103C8T6。CAN1 的内核时钟是 APB1 的 36 MHz，跟第 02 章同一笔。工作点整格照抄罗盘：预分频 9，BS1 = 5，BS2 = 2，SJW = 1。

### 原理与边界

- **一个位。** 时间份额 `Tq = 9 / 36e6 = 250` ns。同步段 1，加 BS1 的 5，加 BS2 的 2，一共 8。位时间 `8 × 250 ns = 2` µs，也就是 500 kbit/s。采样点 `(1 + 5) / 8 = 75%`，落在 1.5 µs。这是主图的正常路径。
- **450 kbit/s。** 想要 10 个时间份额、采样点 70%（BS1 = 6，BS2 = 3）时，预分频是 7.2，不是整数。写成 8 时，`36e6 / (8 × 10) = 450` kbit/s。这是主图的失败路径。1 Mbit/s 那一行（预分频 4，一共 9 个时间份额，采样点 66.7%）留在核心原理的表里，不进四块的工作点，也不把「采样点一般在 75% 到 87.5%」说成那一行的主张。
- **两只工作脚。** BluePill 上用第一种重映射：第 45 脚 PB8 = CAN_RX，第 46 脚 PB9 = CAN_TX。复位默认是第 32 脚 PA11 = CAN_RX，第 33 脚 PA12 = CAN_TX。那一对是第 14 章 USB 的正常路径，这一章不把它画成正常路径。硬件表的 BluePill 行改成 PB8/PB9。PA11/PA12 改成冲突说明。
- **晶振脚。** 第 5 脚 PD0、第 6 脚 PD1 在 LQFP48 上有，它们是 HSE。重映射到这两只脚会停掉 8 MHz 晶振。正文删掉「C8 没有那两只脚」。视频块里的同一句不动。例程里的同一句不动。
- **和 I2C 的重映射。** 第 45 脚和第 46 脚也是第 07 章的 I2C1 重映射。两张主图不把 CAN 和 I2C 画成同时有效。
- **终端。** 总线两端各一只 120 Ω，接在 CANH 与 CANL 之间，不接在 MCU 脚上。MCU 的 PB8/PB9 进收发器的 RXD/TXD，收发器才出 CANH/CANL。两只 120 Ω 并联，直流负载是 60 Ω。60 Ω 不是电缆的特性阻抗。收发器是 3.3 V 还是 5 V，留在硬件节，不进出处卡。
- **总线关闭。** 只有一个节点、又不是回环时，没有应答，发送错误计数涨到 256，节点停止驱动总线。恢复是 128 次、每次 11 个连续隐性位。例程里 ABOM 打开时，硬件自己数，软件不再 `HAL_CAN_Stop` 再 `HAL_CAN_Start`。回环能自发自收，不能代替两端有 120 Ω 的双节点。
- **过滤器。** 32 位掩码里，标准 ID 写入 `FilterIdHigh` 时左移 5 位。这 5 位是高半字里的位置，不是把 21 再左移进 `FilterIdHigh`。不左移时，总线上有帧，邮箱仍是空的。14 组过滤器和 2 个 FIFO 留在边界。F4 的 bxCAN 和 H7 的 FDCAN 在这颗料上不能原样替换。
- **共享中断。** `USB_LP_CAN1_RX0` 与第 14 章是同一条向量。两个例程不要编进同一个工程。这句链接 `rm0008-usb`，不在这一章重画 USB 脚。

### 关键插图

主图文件 `assets/diagrams/sample-13-can-bit.svg`。

图上是一个 2 µs 的位，左边是封装脚：

- 脚位：第 45 脚 PB8 = CAN_RX，第 46 脚 PB9 = CAN_TX，接到收发器。收发器的 CANH、CANL 上，每一端画一只 120 Ω。不把 MCU 脚直接接在这只电阻上。
- **正常路径。** 8 个 250 ns 的时间份额。同步段 1，BS1 = 5，BS2 = 2。采样点标在 1.5 µs，75%。预分频 9。500 kbit/s。SJW = 1。
- **失败路径。** 同一条 36 MHz，预分频写成 8，BS1 = 6，BS2 = 3。位时间对不上 2 µs，速率是 450 kbit/s，采样点 70%。
- **旁注。** 第 32 脚和第 33 脚留作 USB。重映射到第 5 脚和第 6 脚会拆掉 HSE。不画第 07 章的 4.7 kΩ。不画收发器内部电路。

图注写「自绘」，带 RM0008 Rev 21 的 bxCAN 章和 DS5319 Rev 20 表 5。替代文本写出结论：36 MHz 下预分频 9、8 个时间份额是 500 kbit/s；写成预分频 8 和 10 个时间份额是 450 kbit/s；工作脚是第 45 脚和第 46 脚。不写「示意图」。

`can-arbitration.svg` 留作辅图。仲裁和位填充不进这张静态主图。

### 时序或状态

一张表覆盖这一个位。列至少有：预分频、BS1、BS2、时间份额数、位时间、速率、采样点。正常行：9、5、2、8、2 µs、500 kbit/s、75%，时间份额 250 ns。失败行：8、6、3、10、450 kbit/s、70%。脚位行：PB8 收，PB9 发；PA11/PA12 与 USB 冲突。错误行：计数到 256 进入总线关闭；128 次 11 个隐性位之后才可以再驱动。过滤器行：`FilterIdHigh` 左移 5。

### 坑与出处卡

至少这些行：

| 现象 | 处理方向 | 链接 | 允许的主张 |
| --- | --- | --- | --- |
| 示波器或分析仪上是 450 kbit/s | 预分频用 9，BS1 用 5，BS2 用 2 | `#source-rm0008-can` | 8 个时间份额、预分频 9，在 36 MHz 下是 500 kbit/s。10 个时间份额配预分频 8 是 450 kbit/s |
| 单节点、正常模式，发几帧就闭嘴 | 先用回环。上总线时要有应答节点 | `#source-rm0008-can` | 发送错误计数到 256 进入总线关闭。恢复要 128 次、每次 11 个隐性位 |
| 总线上有帧，邮箱是空的 | 标准 ID 写入 `FilterIdHigh` 时左移 5 | `#source-project-examples` | `examples/can-bxcan` 用 `PEER_ID << 5` 填 `FilterIdHigh`。预分频宏是 9 |
| 两端都在报错 | 两端同一组位时间，CANH 与 CANL 之间两端各 120 Ω | `#source-project-examples` | 例程要求两端各一只 120 Ω。这一行不规定电缆特性阻抗，也不规定收发器是 5 V 还是 3.3 V |
| 波形在 PA11/PA12，USB 也失效 | 重映射到第 45 脚和第 46 脚 | `#source-ds5319-usbcan` | 复位默认 CAN 在 PA11/PA12。PB8/PB9 是重映射。PA11/PA12 同时是 USB |
| 重映射到晶振脚之后时钟停了 | 不要把 CAN 放到第 5 脚和第 6 脚 | `#source-ds5319-clock` | LQFP48 第 5 脚是 PD0-OSC_IN，第 6 脚是 PD1-OSC_OUT。这两只脚存在 |
| 和 I2C 重映射抢同一对脚 | 这一对脚只选择 CAN 或 I2C 之一 | `#source-ds5319-i2c` | 第 45 脚 PB8、第 46 脚 PB9 是 I2C1 的重映射。不改写第 07 章那张图 |

1 Mbit/s 那一行、位填充和 CANopen 留在核心原理。

### 短 GIF

辅图 `assets/gif/can-500k.gif`。内容是正常路径：8 个时间份额走过 2 µs，采样点标在 75%，旁边标出 500 kbit/s 和 250 ns。帧数不少于 3、不多于 12。450 kbit/s 和晶振脚只在静态主图上。不替换 `can-arbitration.svg`。

## 第 14 章写什么

订货号仍是 STM32F103C8T6。USB 时钟整格照抄第 02 章和罗盘：`USBPRE = 0`，`72 / 1.5 = 48` MHz。描述符整格照抄附录 D 和 `examples/usb-cdc`。

### 原理与边界

- **48 MHz。** PLL 是 72 MHz。`USBPRE = 0` 再除以 1.5，USB 时钟是 48 MHz。`USBPRE = 1` 不除，USB 时钟是 72 MHz。主机在读描述符时失败。这是主图的失败路径。不重画时钟树。
- **两只脚。** 第 32 脚 PA11 = USB_DM，第 33 脚 PA12 = USB_DP。全速的 1.5 kΩ 上拉接在 D+ 和 3.3 V 之间，也就是第 33 脚这一侧。接到第 32 脚上，主机不会按这颗全速设备来认。BluePill 板载这只电阻时，软件断开不一定还能把 D+ 放掉。片内上拉只有 RM0008 或 DS5319 印出了才写进 snapshot。没印出阻值，图上的 1.5 kΩ 仍标成罗盘里的数，出处卡那一行不升格成新的电气限额。
- **设备，不是主机。** 这颗料的 USB 是全速设备，12 Mbit/s 这一档。低速 1.5 Mbit/s 不是它的工作模式。480 Mbit/s、OTG 和 ULPI 在这颗料上作废。F4 的 OTG 留在核心原理。
- **18 字节和 67 字节。** 设备描述符长度 `0x12`。`bMaxPacketSize0` 是 64。VID 是 `0x1209`，PID 是 `0x0001`。这是本仓库实验号。PID `0x0001` 没有当作量产登记，量产前要换成自己的号。ST 例程常见的 `0x0483/0x5740` 不是这一份描述符。配置集合的 `wTotalLength` 是 `0x0043`，即 67，不是 18。`bMaxPower = 0x32`，单位 2 mA，所以是 100 mA。
- **包长。** 全速批量和中断的上限都是 64 字节。1023 只属于全速等时。把中断或批量的 `wMaxPacketSize` 写成 1023 是失败旁注。例程的通知端点是 8 字节，批量端点是 64 字节。8 没有超出 64 的上限。
- **共享脚和共享中断。** PA11/PA12 的 CAN 默认功能在第 13 章已经移走。本图只画 USB。`USB_LP_CAN1_RX0` 与 CAN 接收是同一条中断，两个例程不要编在一起。
- **差分走线。** 线宽和特性阻抗不进四块，除非 AN4879 或 DS5319 印出了欧姆数并写进 snapshot。没印出来，就不编 90 Ω 或其他数。AN4879 不新开 id。

### 关键插图

主图文件 `assets/diagrams/sample-14-usb-enum.svg`。

图上是插上之后的第一眼：

- 脚位：第 32 脚 PA11 = DM，第 33 脚 PA12 = DP。1.5 kΩ 从 3.3 V 接到 DP。USB 时钟标成 48 MHz，`USBPRE = 0`。
- **正常路径。** 主机看见 D+ 被拉高。设备描述符 18 字节，VID/PID `0x1209/0x0001`，`bMaxPacketSize0` 64。配置集合长度 67。`bMaxPower` 标成 100 mA。
- **失败路径。** `USBPRE = 1`，时钟变成 72 MHz，描述符读失败。
- **旁注。** 1.5 kΩ 接到 DM。批量或中断包长写成 1023。描述符抄成 `0x0483/0x5740`。不画 CAN 收发器。不画 ULPI。

图注写「自绘」，带 RM0008 Rev 21 的 USB 设备章、第 02 章已经冻结的 `USBPRE`，以及本仓库 `usb-cdc`。替代文本写出结论：全速要 48 MHz；D+ 上拉在第 33 脚；这份描述符是 18 字节设备加 67 字节配置集合，VID/PID 是 `0x1209/0x0001`。不写「示意图」。

`usb-enumeration.svg` 留作辅图。

### 时序或状态

一张表覆盖时钟和这份描述符。列至少有：项目、值、对错。必须有的行：`USBPRE = 0`，48 MHz，正常；`USBPRE = 1`，72 MHz，失败。描述符行：长度 18，`bMaxPacketSize0` 64，VID `0x1209`，PID `0x0001`。配置行：`wTotalLength` 67，`bMaxPower` `0x32` = 100 mA。包长行：批量和中断上限 64；1023 只属于等时；通知端点 8 是允许的。脚位行：第 32 脚 DM，第 33 脚 DP，上拉在 DP。

### 坑与出处卡

至少这些行：

| 现象 | 处理方向 | 链接 | 允许的主张 |
| --- | --- | --- | --- |
| 设备管理器里描述符请求失败 | `USBPRE` 保持 0，USB 时钟 48 MHz | `#source-rm0008-rcc` | `USBPRE=0` 时 72 MHz ÷1.5 = 48 MHz。`USBPRE=1` 得到 72 MHz |
| 主机完全看不到设备 | 上拉接在第 33 脚 D+，不要接到 DM。阻值用罗盘里的 1.5 kΩ | `#source-ds5319-usbcan` | 第 32 脚 PA11 的复用含 USB_DM，第 33 脚 PA12 的复用含 USB_DP。这一行不证明上拉阻值 |
| 枚举到的是别人的 VID | 用本仓库的 `0x1209/0x0001` | `#source-project-examples` | `examples/usb-cdc` 的设备描述符是 18 字节。VID/PID 是 `0x1209/0x0001`，不是 `0x0483/0x5740`。PID 只给实验板占位 |
| 配置集合长度和字节数对不上 | `wTotalLength` 写成 67，不要写成 18 | `#source-project-examples` | 配置描述符里的总长是 `0x0043`。`bMaxPower` 的 `0x32` 是 100 mA |
| 中断或批量端点写成 1023 | 全速这两类的上限是 64。1023 只给等时 | `#source-project-examples` | 例程批量端点是 64 字节，通知端点是 8 字节 |
| 和 CAN 例程链在一起，接收中断串了 | 两个例程分开。CAN 不要留在 PA11/PA12 | `#source-rm0008-usb` | 向量名以 snapshot 里印出的为准。默认是 `USB_LP_CAN1_RX0` |

差分阻抗和 USB-IF 的 10 ms 复位留在核心原理。10 ms 不进出处卡，除非以后有允许吸收的来源，这一批不追加。

### 短 GIF

辅图 `assets/gif/usb-48m.gif`。内容是正常路径：D+ 经上拉被主机看见，时钟标成 48 MHz，随后标出描述符 18 字节和配置集合 67 字节。帧数不少于 3、不多于 12。72 MHz 和接错的上拉只在静态主图上。不替换 `usb-enumeration.svg`。

## 第 15 章写什么

订货号仍是 STM32F103C8T6。分组跟第 04 章同一笔：`NVIC_PRIORITYGROUP_4`，4 位抢占，0 位子优先级。不把 167 ns 搬进来。

### 原理与边界

- **节拍。** `configTICK_RATE_HZ = 1000`，一个 tick 是 1 ms。短于 1 ms 的期限不是内核保证。SysTick 归内核。HAL 的时基改到 TIM4，这是 `examples/freertos-task` 的 README 已经写明的那一只，不是笼统的 TIMx。两家都占 SysTick 时，`HAL_Delay` 卡住。这是旁注里的失败。
- **两个方向。** 任务优先级数值大的先跑。KEY 是 2，LED 和 UART 是 1，同时就绪时先跑 KEY。把任务优先级当成 NVIC、以为 1 比 2 更优先，是主图的失败路径。NVIC 仍是数值小的更优先。空闲任务是 0。
- **FromISR。** `5 << (8 − 4) = 0x50`。调用 FromISR 的中断，抢占优先级数值要大于等于 5。例程把 `EXTI0` 设成 5，这是正常路径。设成 0 会停在 `configASSERT`。数值 4 同样过急，不因为「不是 0」就合法。PendSV 和 SysTick 放在最低紧迫度。分组若改掉，`0x50` 这支移位不再直接可比。分组保持 `GROUP_4`。
- **字。** `xTaskCreate` 的栈深度是字，一字 4 字节。LED 128 字 = 512 字节。KEY 192 字 = 768 字节。UART 256 字 = 1024 字节。把 128 当成 128 字节，是旁注里的失败。实验节里的 64 字溢出留在实验，不进主图。
- **延时。** 先干 3 ms 再 `vTaskDelay(10)`，从调用时再等 10 个 tick，周期接近 13 ms。`vTaskDelayUntil` 的 10 ms 把周期钉在 10 ms。软件定时器回调里不再 `vTaskDelay`。
- **互斥量。** 保护共享资源用互斥量，有优先级继承。二值信号量没有继承，只适合通知。这句进坑卡，不进主图的波形。
- **没有 FPU。** Cortex-M3 的这颗 C8 没有浮点单元。坑表里「打开 FPU 上下文」删掉或改成：这句在 STM32F103C8T6 上作废。不画一条打开 FPU 的正常路径。
- **不进第 28 章。** heap_4 只写「会合并相邻空闲块」这一句。不搬 17.2% 的任务预算，不比较 RT-Thread 和 Zephyr。

### 关键插图

主图文件 `assets/diagrams/sample-15-rtos-prio.svg`。

图上是 1 ms 节拍上的一次选择：

- 时钟：SysTick 1 ms。HAL 时基标成 TIM4，不占 SysTick。
- **正常路径。** KEY 优先级 2 在跑，LED 优先级 1 在等。LED 的栈标成 128 字 = 512 字节。`EXTI0` 的抢占优先级是 5，可以 `xQueueSendFromISR`。旁边标 `0x50`。
- **失败路径。** 同一条 EXTI 的抢占优先级写成 0，调用 FromISR，停在 `configASSERT`。
- **旁注。** 把 128 字当成 128 字节。HAL 仍挂在 SysTick 上。以为任务优先级 1 比 2 更优先。不画 8 寄存器入栈。不画 167 ns。

图注写「自绘」，带 FreeRTOS Kernel V11.3.2 的移位和本仓库 `freertos-task`。替代文本写出结论：一个 tick 是 1 ms；任务优先级 2 先于 1；128 字是 512 字节；FromISR 的数值优先级要大于等于 5。不写「示意图」。

`freertos-scheduler.svg` 留作辅图。

### 时序或状态

一张表用这一个毫秒。列至少有：对象、数值、谁先走。必须有的行：tick，1000 Hz，1 ms。任务行：优先级 2 先于优先级 1。栈行：128 字 = 512 字节，192 字 = 768 字节，256 字 = 1024 字节。中断行：数值 5 可以调用 FromISR；数值 0 停在 `configASSERT`；`0x50 = 5 << 4`。时基行：内核用 SysTick，HAL 用 TIM4。延时行：工作 3 ms 再 `vTaskDelay(10)`，周期接近 13 ms；`vTaskDelayUntil` 的 10 ms 仍是 10 ms。

### 坑与出处卡

至少这些行：

| 现象 | 处理方向 | 链接 | 允许的主张 |
| --- | --- | --- | --- |
| `HAL_Delay` 卡住，或调度器起不来 | HAL 时基改到 TIM4，SysTick 留给内核 | `#source-project-examples` | `examples/freertos-task` 的 README 把时基源写成 TIM4 |
| 一进中断就停在 `configASSERT` | `EXTI0` 的抢占优先级写成 5 或更靠后的数 | `#source-freertos-syscall` | 4 位优先级时，5 左移 4 位是 `0x50`。数值更小的中断不得调用 FromISR |
| 优先级 1 的任务压过优先级 2 | 任务优先级数值大的先跑。这和 NVIC 相反 | `#source-freertos-syscall` | 任务优先级数值更大的先跑 |
| 例程里 KEY 没有压过 LED | KEY 写 2，LED 和 UART 写 1 | `#source-project-examples` | `examples/freertos-task` 里 KEY 的任务优先级是 2，LED 和 UART 是 1 |
| 栈说明书写 128，一打印就溢出 | 128 的单位是字，等于 512 字节 | `#source-project-examples` | LED 128 字，KEY 192 字，UART 256 字 |
| 按键中断一进来就断言 | `EXTI0` 的抢占优先级写成 5 | `#source-project-examples` | 例程把 `EXTI0` 的抢占优先级设成 5 |
| 两个任务的串口叠在一起 | 用互斥量，不用二值信号量来保护资源 | `#source-freertos-syscall` | 互斥量有优先级继承。二值信号量没有 |
| 周期越来越长 | 固定周期用 `vTaskDelayUntil`。`vTaskDelay(10)` 是再等 10 ms | `#source-freertos-syscall` | 一个 tick 是 1 ms 时，调用前已经花掉的时间不包含在 `vTaskDelay` 里 |

heap 的五种实现、软件定时器回调和 FPU 作废句留在核心原理。FPU 那一句不进出处卡。

### 短 GIF

辅图 `assets/gif/rtos-tick.gif`。内容是正常路径：节拍每 1 ms 走一格，优先级 2 占着 CPU，优先级 1 在等，栈标成 128 words = 512 bytes。帧数不少于 3、不多于 12。`configASSERT` 和 SysTick 冲突只在静态主图上。不替换 `freertos-scheduler.svg`。

## 插图标准

沿用总纲和 Batch4 的逼真、翔实、生动、可印刷、自绘。主图和短 GIF 分开。简化示意图可以留在章内当辅图，不能充当关键插图的主图。

静态主图要让人能对着封装和仪器核对：

- 第 12 章画出 64 KB 的地址边界、1 KB 页和半字，不画成两只没有地址的方框。
- 第 13 章画出 250 ns 的时间份额、2 µs 的位、120 Ω 接在 CANH 与 CANL 上，以及 MCU 脚与总线之间的收发器。不把 PB8 直接画到终端电阻上。
- 第 14 章画出第 32 脚、第 33 脚、D+ 上的 1.5 kΩ 和 3.3 V，以及 18 与 67 这两个长度。
- 第 15 章画出 1 ms 的节拍、优先级数字和「字 → 字节」。不画成没有数字的三个圆圈。

静态主图的文件规则：

- 用 `tools/svgkit.py`，生成脚本是 `tools/gen_sample_figures.py`。四章各一张，中英引用同一文件。中文路径 `../assets/diagrams/...`，英文路径 `../../assets/diagrams/...`。第 12 章只有在单张超过 60 KB、拆图之后才增加第二张 `sample-12-iap-vectors.svg`。
- 不调用 `Svg.footer()`。落款用脚本里已有的 `_credit()`：左侧是文档号，右侧是「自绘 · 静态 · CC BY 4.0」。
- 没有 `<animate`、`@keyframes`、`animation:`。图上同时有正常路径和失败路径。
- 替代文本写结论。图注写「自绘」，不写「实拍」「手册截图」「矢量动画」。
- 单张小于 60 KB。放不下就拆成主图加局部，每张仍争取小于 60 KB。拆开仍超过时，在实施 PR 里写出字节数和原因，不把图画回简笔，也不把 60 KB 改成仓库新默认值。
- 登记进 `assets/README.md` 第四节，和已有的 `sample-00` 到 `sample-11` 主图并列。`gen_sample_figures.py` 那一行注释补上第 12、13、14、15 章。

短 GIF：

- 四条都走 `tools/gen_gifs.py`，加入 `BUILDERS`，这样 `tools/check_assets.py` 能逐像素对上重新生成的帧。GIF 上的字用 ASCII。
- 每条少于 500 KB，帧数见上面四节。图注写明它是网页和公众号辅图，印刷以静态主图为准。
- `gen_gifs.chrome()` 自带的页脚可以留在 GIF 里。那条页脚不是静态主图的 `Svg.footer()`。
- 不改已有 16 个 BUILDERS 的像素：`led-blink`、`pwm-breath`、`uart-bits`、`i2c-timing`、`dma-ring`、`sar-adc`、`nvic-preempt`、`uart-idle`、`clock-css`、`pwm-1khz`、`spi-jedec`、`adc-sample`、`swd-fetch`、`i2c-addr`、`dma-cndtr`、`iwdg-1s`。不重跑它们来换画面。
- `tools/svg2gif.py` 这一批不当成必经步骤，也不为了它去改 CI。`assets/README.md` 第五节把「上面 16 张 GIF」改成「上面 20 张 GIF」。

PDF 关掉动画之后，读者只看静态主图和图注，就能指出失败发生在哪一段。第 12 章是「钥匙反序，或末页写成 `0x0801FC00`，或 `VTOR` 仍为 0」。第 13 章是「预分频 8 且 10 个时间份额，500 kbit/s 变成 450 kbit/s」。第 14 章是「`USBPRE = 1`，USB 时钟是 72 MHz」。第 15 章是「抢占优先级 0 调用了 FromISR」。

## 工作流与 PR 节奏

### 本 PR（设计）

只新增 `docs/superpowers/specs/2026-10-25-classic-encyclopedia-batch5-12-13-14-15-design.md`。不改 `docs/12`、`docs/13`、`docs/14`、`docs/15` 和 `docs/en/` 的章节。不改 `stm32-book/`、`CREDITS.md`、`assets/`、`tools/`。不升版本，不打 tag，不发 Release。不新增 `docs/superpowers/plans/` 下的实施计划。不改样式，不重画海报。本 PR 等人审阅规格后再合入，不在 CI 变绿后自动合。

### 实施 PR（下一轮，不在本 PR）

顺序固定：

1. **核对扫描。** 写出 `2026-10-25-batch5-12-13-14-15-lock.json`。章号保持 12、13、14、15。
2. **许可门。** 写出 `2026-10-25-batch5-12-13-14-15-source-list.json`。先有清单，再改正文。
3. **静态主图和短 GIF。** 先提交 SVG、GIF 和生成脚本，再写正文。主图不依赖 GIF。
4. **中英加厚。** 八份 Markdown 一起提交。视频块以内的字节保持不变。文件 `00` 到 `11`，以及 `16` 到 `28`，正文 diff 为空。
5. **登记。** 新来源追加进两份 manifest。更新这四章罗盘的来源数组。`CREDITS.md` 第六节增加 v1.3.0 小节，并把静态框图改为 22 张、光栅动画改为 20 个。若拆出 `sample-12-iap-vectors.svg`，静态框图改为 23 张。`revisions.json` 在条目最前加上 1.3.0，日期写死 `2026-10-25`。两份 manifest 的 `version` 改为 `1.3.0`，`date` 改为 `2026-10-25`。`stm32-book/README.md` 的当前版本句改为 **v1.3.0 · 2026-10-25**。发布一节里的 tag 名改成 `v1.3.0`，并在现有「也不要把 1.2.8 的产物标成 1.2.9」之后加上「也不要把 1.2.9 的产物标成 1.3.0」。这一步仍不创建 tag，也不创建 Release。修订说明只写这四章加厚了什么，用文件名前缀。中英各两句，例如：第 12 章写上中容量 1 KB 页，APP 从 `0x08004800` 起、长度 `0xB800`，跳转要装入第 0 字和第 1 字。第 13 章写上预分频 9、8 个时间份额是 500 kbit/s，预分频 8 且 10 个时间份额是 450 kbit/s，工作脚是 PB8/PB9。第 14 章写上 `USBPRE=0` 得到 48 MHz，描述符是 18 字节和 67 字节，VID/PID 是 `0x1209/0x0001`。第 15 章写上 1 ms 节拍、128 字等于 512 字节、FromISR 的数值优先级要大于等于 5，HAL 时基是 TIM4。英文用同样的事实。
6. **测试。** 新增 `stm32-book/tests/test_batch5_chapters.py` 和 `stm32-book/tests/test_batch5_sources.py`，照着 Batch4 测试检查四块、共享数字、主图禁词和许可门。视频块里的旧旁白不拿来判失败。不放宽 `test_sample_chapters.py`、`test_batch2_chapters.py`、`test_batch3_chapters.py` 和 `test_batch4_chapters.py`。`test_build.py` 里当前版本从 `1.2.9` 改为 `1.3.0`：`assert_version_history_and_index` 的元组在 `1.2.9` 之前加上 `1.3.0`，并断言 `1.3.0` 出现在 `1.2.9` 之前。修订列表以 `1.3.0` 起头。两份整书 HTML 含 `<strong>v1.3.0</strong>`。`test_visual_polish_version_is_1_2_0` 改为核对当前条目是 1.3.0，日期是 2026-10-25。现在对 `entries[0]` 的 1.2.9 海报两句改去核对 `entries[1]`。现在对 `entries[1]` 的 1.2.8 密度两句改去核对 `entries[2]`。现在对 `entries[2]` 的 1.2.7 浅色两句改去核对 `entries[3]`。现在对 `entries[3]` 的 1.2.6 封面两句改去核对 `entries[4]`。现在对 `entries[4]` 的 1.2.5 令牌两句改去核对 `entries[5]`。现在对 `entries[5]` 的 1.2.4 排版两句改去核对 `entries[6]`。现在对 `entries[6]` 的 1.2.3 两句改去核对 `entries[7]`。现在对 `entries[7]` 的 1.2.2 两句改去核对 `entries[8]`。现在对 `entries[8]` 的 1.2.1 指南两句改去核对 `entries[9]`。现在对 `entries[9]` 的 1.2.0 两句改去核对 `entries[10]`。README 的断言改成当前版本句、`版本号已经是 1.3.0`、`也不要把 1.2.9 的产物标成 1.3.0` 和 `打 tag \`v1.3.0\``。不删 `0x271`、`167 ns`、账本名和出版书签长度为 44 的断言。不改 CSS 哈希一类的视觉契约。不新增读取 `CONTENT_GUIDE.md` 的测试。
7. **CI 变绿之后停下来等人复审。** 复审对象是构建出的中英 HTML 里的这四章。人接受之前不合入，也不开下一批章。Book CI 变绿不等于可以自动 squash 合入。

实施 PR 的 diff 可以碰这四章中英正文、两份 manifest 的新 `sources` 和这四章罗盘、新图与生成脚本、`assets/README.md`、`CREDITS.md`、版本与修订、新的锁定文件和来源清单、新测试，以及 `test_build.py` 里的版本字符串。不碰其余章的正文，不改 `build_html.py`，不改样式文件，不改 `assets/video/`。

## 验收

### 本设计 PR

- 相对基线 `adc5cd7`，只新增 `docs/superpowers/specs/2026-10-25-classic-encyclopedia-batch5-12-13-14-15-design.md`。
- 章节、`stm32-book/`、资产、工具和 `CREDITS.md` 与基线 `adc5cd7` 相同。
- 没有新的 SVG 或 GIF，版本号仍是 1.2.9。没有实施计划文件。没有样式 diff，没有海报 diff。

### 实施 PR

- 中文四章各有且仅有一次：`## 原理与边界`、`## 关键插图`、`## 时序或状态`、`## 坑与出处卡`。英文对应四个标题同样各一次。
- 四章都不再有 `## ⚠️ 常见坑与排查` 或 `## ⚠️ Pitfalls and troubleshooting`。
- 每章关键插图的第一张图是对应的静态 SVG。图上能看出正常路径和失败路径。GIF 不是这一节唯一的图。
- 视频块以外，中英都有这些数字，而且彼此一致：
  - 第 12 章：`0x08000000`、`0x08004000`、`0x08004800`、`0x08004804`、`0x0800FC00`、`0x08010000`、`0xB800`、`0x45670123`、`0xCDEF89AB`、`1` KB、`64`、`16`、`2`、`46`。四块写明这颗料是中容量。四块可以写 `0x0801FC00` 和按字节编程在 C8 上作废。四块不把无保护写成 `0xAA`。
  - 第 13 章：`36`、`9`、`5`、`2`、`8`、`250` ns、`2` µs、`500`、`75`、`8` 与 `10` 个时间份额下的 `450`、`70`、`256`、`128`、`11`、第 45 脚、`PB8`、第 46 脚、`PB9`、第 32 脚、`PA11`、第 33 脚、`PA12`、第 5 脚、第 6 脚、`120`。四块写明 PD0/PD1 在封装上存在。四块不把 60 Ω 写成电缆特性阻抗。
  - 第 14 章：`USBPRE`、`0`、`1`、`48`、`72`、`18`、`67`、`0x0043`、`0x1209`、`0x0001`、`64`、`0x32`、`100`、`1023`、`8`、第 32 脚、第 33 脚、`1.5`。四块写明 C8 的 USB 是设备。四块不把 `0x0483/0x5740` 写成这份描述符。
  - 第 15 章：`1000`、`1` ms、`GROUP_4`、`0x50`、`5`、`4`、`128`、`512`、`192`、`768`、`256`、`1024`、任务优先级 `2` 与 `1`、`TIM4`、`13`、`10`。四块写明任务优先级和 NVIC 的方向相反，并且这颗料没有 FPU。167 ns 和 17.2% 不出现在这一章的四块里。
- 第 14 章和第 15 章引用附录 D 的格子时整格照抄，不改附录 D 正文。第 12 章引用 64 KB 和第 01 章的两字时不改那两章。第 13 章引用 36 MHz 和第 5、第 6 脚时不改第 02 章。
- 静态 SVG 小于 60 KB，不含动画标记，含「自绘」，不含「实拍」和「矢量动画」。四条新 GIF 小于 500 KB，并且在 `BUILDERS` 里。已有 16 条 GIF 的像素与基线相同。四张旧动画 SVG 的字节与基线相同。`assets/video/` 与基线相同。
- 新 `#source-` 都能在构建出的 HTML 里找到 `id="source-..."`。已有 `rm0008`、`ds5319`、`rm0008-rcc`、`ds5319-clock`、`ds5319-i2c`、`ds5319-swd`、`pm0075-rdp`、`pm0056`、`pm0056-vector`、`pm0056-nvic`、`project-examples`、`rm0090`、`usb20`、`freertos-priority`、`freertos-1132`、`an2606`、`an3965` 的对象与基线逐字段相同。
- 附录 D 已有各行和附录 A 的正文 diff 为空。`test_build.py` 对 `0x271`、`167 ns` 和出版书签条数的断言仍在。样式文件和 `build_html.py` 的 diff 为空。
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

1. **脚号。** 默认第 32 脚 PA11、第 33 脚 PA12，第 45 脚 PB8、第 46 脚 PB9。实施时打开与 `ds5319-clock` 同一份 DS5319 Rev 20 表 5。印出的脚号不同就改脚号，信号名按印出的复用列，并在实施 PR 里写明。不沿用一份没核对过的脚号去否定表 5。
2. **片内上拉。** 只有 RM0008 或 DS5319 印出了阻值，才写进 `rm0008-usb` 或 `ds5319-usbcan` 的 snapshot。印出的不是 1.5 kΩ，片内那只用印出的数。没印出阻值，图上仍按罗盘标 1.5 kΩ，坑卡里「上拉接在 D+」可以留下，但主张写成「罗盘已写 1.5 kΩ；手册这一版没有把阻值收进出处卡」。不编一个新的千欧。
3. **USB 章号和向量名。** 默认 RM0008 第 23 章，向量名 `USB_LP_CAN1_RX0`。印出的标题或名字不同就改 snapshot，48 MHz 和「设备不是主机」不变。
4. **CAN 章号和重映射编码。** 默认第 21 章。印出的章号或 `CAN_REMAP` 编码不同就用印出的。500 kbit/s 仍是预分频 9 和 8 个时间份额。不编基址。
5. **过滤器的 5 位。** 默认与例程一致：标准 ID 放在 `FilterIdHigh`，左移 5。RM0008 印出的位若对不上这 5 位，用印出的位，并在实施 PR 里写明例程的 5 位对应高半字的哪一段。不把 21 位再左移进 `FilterIdHigh`。
6. **FreeRTOS 的库优先级。** 默认公式是左移 `(8 − 4)`，本仓库 EXTI 用 5，得到 `0x50`。V11.3.2 演示工程印出的库优先级若不是 5，snapshot 记印出的公式，例程的 5 不改。
7. **主图体积。** 先拆图。第 12 章的第二张只允许叫 `sample-12-iap-vectors.svg`。拆开仍超过 60 KB 时在实施 PR 里说明，不降低画法标准。
8. **版本号。** 实施时升到 1.3.0，不写成 1.2.10。日期写 `2026-10-25`。本设计 PR 不升版本。
9. **图目录。** 这一批不加。
10. **下一批章号。** 仍是 4 章，到下一次设计再锁。本文件不预选 `16` 或 `28`。
11. **同一对脚。** 第 13 章主图主张 PB8/PB9 上的 CAN。第 14 章主图主张 PA11/PA12 上的 USB。第 07 章已经主张 PB8/PB9 不是 I2C 的正常路径。三张图都不把两种功能画成同时有效。

## 英文提要

Thicken only chapter files 12 (Flash and IAP), 13 (bxCAN), 14 (USB device), and 15 (FreeRTOS), in Chinese and English, on top of v1.2.9 (`adc5cd7`, PR #53). Chapters 00 through 11 are already thick. Do not retitle this batch as the RTOS survey in file 28. Density pass F already tightened whitespace in 1.2.8; this batch does not touch CSS. The 29 lecture posters in 1.2.9 stay as they are, including the video-block narration. Use the same four sections as the thick chapters. Each chapter gets one printable static SVG from `gen_sample_figures.py`, with a normal path and a failure path, and no `Svg.footer()`. Chapter 12 draws the 64 KB medium-density map: 1 KB pages, keys `0x45670123` then `0xCDEF89AB`, app at `0x08004800` for `0xB800` bytes. The failure is a reversed key, a byte program, `VTOR` left at 0, or a last page at `0x0801FC00`. Calling this part low-density is void; the page size stays 1 KB. Chapter 13 draws one 2 µs bit at 36 MHz: prescaler 9, eight 250 ns quanta, sample at 75 percent, 500 kbit/s, on pins 45 PB8 and 46 PB9, with 120 Ω across CANH and CANL at each end of the bus. Prescaler 8 and ten quanta is the 450 kbit/s failure. Pins 5 and 6 exist; they are the HSE pins, not absent. Chapter 14 draws USB on pins 32 PA11 (DM) and 33 PA12 (DP), with the 1.5 kΩ pull-up on D+. `USBPRE=0` is 48 MHz. `USBPRE=1` is 72 MHz and fails enumeration. The repo descriptor is 18 bytes plus a 67-byte configuration set, VID/PID `0x1209/0x0001`, not `0x0483/0x5740`. Chapter 15 draws a 1 ms tick, task priority 2 ahead of priority 1, a 128-word stack as 512 bytes, and EXTI priority 5. Priority 0 calling FromISR stops in `configASSERT`. The HAL time base is TIM4. This part has no FPU. One short GIF per chapter is auxiliary only. The existing 16 GIF builders and the four chapter animations stay as they are. Register five new sources by appending ids. Bump the book to 1.3.0 on 2026-10-25 during implementation, do not tag or release, and stop for human review before squash-merge. This design PR only adds this file.

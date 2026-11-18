---
title: "资料、学习路线与开源地图"
platforms: [generic]
---

# 资料、学习路线与开源地图

全书最后一章回答三个「往后怎么办」：路线怎么走（三阶段计划与 L0–L5 证据级别）、资料怎么读（手册六类与查手册三步法）、开源怎么用（源码仓库、开源书/课程、配套代码与社区文章）。它同时是两本姊妹书学习路线的合并口径：两源在「先学 HAL 还是先学寄存器」上建议相反，统一口径写在这里并声明取舍。

这里没有板级实测。三阶段周数表是**计划表**（文档推导，逐周自测题的答案在 [附录 C](../appendix/C-exercises-answers.md)）；采购价格是估算区间，来源自注「以当日价格为准」；开源库定位与工具选型按来源卡口径；开源仓库星标数全部带抓取日期 2026-10-26（附录 F 双源同日核对）。社区书/课/配套代码的星标取 2026-11-15，许可取仓库根文件；这一组数字和附录 F 的 2026-10-26 快照不同日，只用来看量级。BOOT 与首次点灯的技术正文归 [v1 第 8 章](../v1-drivers/08-architecture-memory-clock.md) 与 [v1 第 9 章](../v1-drivers/09-gpio.md)，这里只留路线索引。

> 版本口径：D00《如何学习 STM32》（`docs/00-如何学习STM32.md`）、D20《学习资源与工具链》（`docs/20-学习资源与工具链.md`）、mbF 起步区并入；手册命名六类（RM/DS/PM/AN/UM/ES）按 D20 正文表统一（源章「学习目标五种」的内部不一致在此修正为六类）。手册文档号（DS5319/RM0008/PM0056/CubeF1）与根书注册表一致（附录 E）。

## 本章罗盘

- **问题**：三阶段路线（4/6/8 周）的过关判据与前置知识五块的「够用」标准；L0–L5 六级证据怎么判定、对应哪些卷章；三种开发方式（寄存器/SPL/HAL+LL）的六维对比，两书相反的入门建议如何统一。手册六类各查什么、三步法怎么走；工具选型两表的预算口径；开源仓库、开源书/课程、配套代码与社区文章怎么选、怎么读、怎么问；生态数字为什么必须带抓取日期。
- **交付**：能按三阶段表给自己排计划并写出过关判据；能指出自己停在 L0–L5 哪一级，并写出下一级缺的证据；能用前置知识表自评「够用即可」；能按统一口径选择入门路线并说出取舍理由；能按六类命名表挑对手册并用三步法查到 TIM1 占空比/PA11 USB/F4 DMA FIFO 三个示例；能从四类社区资源里选一本开源书或课程，说明它的许可边界；能给出两板（BluePill 起步线/霸天虎+实战派线）的采购清单；能按提问五件事提一个可回答的问题。
- **级别**：L5 交付。证据位置：「测量与证据」与「离开检查」；读完留下自己的三阶段计划与过关判据、L0–L5 自评与下一级缺口证据，以及一本开源书的许可边界说明。
- **旅程导航**：上一章（[第 45 章](./45-troubleshooting-handbook.md)）你手里有从现象翻到章锚点的分诊路径与三条抽查样例的核对记录；本章结束多了自己的三阶段计划与过关判据、L0–L5 自评与下一级缺口（周数是计划表、采购价是估算区间、星标数带抓取日期）——L5 的「失败经验可查」升到「路线自己能排」：十八周每周绑一个可展示物、六级按证据划分不按章数、手册六类与查手册三步法、开源资源的许可边界，这些是你自己的排期与自评不是别人给的评级；终点回看起点，十八周排期接回[第 0 章](../onramp/00-from-box-to-blink.md)的开箱闭环。
- **开源读法**：从四类社区资源里挑一本（如 `rust-embedded/discovery`），按「编译一条命令 → 目录结构 → 最小例程」的读法走一遍，许可读仓库根文件原文；地址、时钟与位段仍回对应 RM/DS。
- **边界**：这里属于路线与资料层；BOOT、首次点灯、构建命令的技术正文归 v1 各章（这里只留索引）；L0–L5 的定义与卷章映射在这里；全量源码仓库表与知识点在 附录 F；手册来源注册表在 附录 E；生态数量口径沿 [第 27 章](../v3-rtos/27-rtos-comparison-selection.md)。视频块、公众号手机阅读版、英文版链接不保留。
- **依据锚点**：D00、D20（`docs/`）、mbF 起步区（`mcu/mcu-book/book/F-常见问题.md` 并入部分）。上游对账：SPL 停更与 [卷 0 第 7 章](../v0-foundations/07-build-systems-legacy.md) 口径一致；F1 DMA 无 FIFO/F4 有与 [v1 第 14 章](../v1-drivers/14-dma.md)、[第 33 章](../v4-platforms/33-network-protocol-stack.md) 一致。

## 先做出来

### 1. 三阶段路线与过关判据

| 阶段 | 周数 | 主题 | 过关判据 |
| --- | --- | --- | --- |
| 入门 | 4 周 | 环境/点灯/串口/中断 | 首次点灯三道门槛全过；串口回环可复查 |
| 进阶 | 6 周 | 定时器/ADC/DMA/总线/RTOS 入门 | 每个外设一次「押注→测量→对账」记录 |
| 实战 | 8 周 | 综合项目/交付验收 | 一份交付包（[第 42 章](../v6-labs-projects/42-project-delivery-acceptance.md) 五件套） |

三阶段展开成十八周，每周绑定章、配套例程（全表见[附录 B](../appendix/B-project-index.md)）与一个可展示物——周计划是文档推导（计划表），里程碑物的判据都指向对应章的离开检查与例程 README：

| 周 | 章 | 配套例程 | 你手里多了什么（可展示物） |
| --- | --- | --- | --- |
| 1 | [卷 0 第 7 章](../v0-foundations/07-build-systems-legacy.md) | `gpio-blink` | 构建日志 + PC13 约 1 Hz 闪烁——板上的灯第一次听你的 |
| 2 | [v1 第 9 章](../v1-drivers/09-gpio.md) | `gpio-blink` 外接灯 | PA0 经 270 Ω 点亮外接 LED，会算限流电阻 |
| 3 | [v1 第 13 章](../v1-drivers/13-uart-framed-protocol.md) | `uart-dma-idle` | `AT` 握手返回 `OK`——第一次跟芯片对话 |
| 4 | [v1 第 10 章](../v1-drivers/10-interrupts-nvic-exti.md) | `exti-key` | 按键事件进中断、计数可读；收口 L0→L1 证据包 |
| 5 | [v1 第 12 章](../v1-drivers/12-timers-pwm.md) | `timer-pwm` | 1 kHz PWM，占空比随 CCR 连续变化 |
| 6 | [v1 第 15 章](../v1-drivers/15-adc-dac-sampling.md) | `adc-dma` | 3 通道采样，输入变化与对应通道一致 |
| 7 | [v1 第 16 章](../v1-drivers/16-i2c-spi.md) | `i2c-oled` | OLED 显示并持续刷新 |
| 8 | [v1 第 16 章](../v1-drivers/16-i2c-spi.md) | `spi-flash` | JEDEC ID `0xEF4017`，跨页写逐字节一致 |
| 9 | [ch21–22](../v3-rtos/21-why-rtos.md) | `freertos-task` | 三任务运行、队列阻塞、按键唤醒 |
| 10 | 阶段收口 | — | L1→L2 证据包：时序图 + 缓冲区状态 + 代码路径 |
| 11 | [v1 第 11 章](../v1-drivers/11-systick-timebase-rtc.md)、[第 18 章](../v2-reliability/18-low-power.md) | `rtc-alarm` | STOP 后按计划唤醒，VBAT 下时间连续 |
| 12 | [v1 第 17 章](../v1-drivers/17-flash-iap-ota.md) | `iap-bootloader` | 镜像校验通过跳转；损坏镜像不跳 |
| 13 | [第 35 章](../v4-platforms/35-can-usb-fieldbus.md) | `can-bxcan` | 环回自收；双节点有 ACK |
| 14 | [第 35 章](../v4-platforms/35-can-usb-fieldbus.md) | `usb-cdc` | 主机枚举出 CDC，双向字节传输 |
| 15 | [第 36 章](../v5-motion/36-motor-driver-power.md) | `motor-dc-speed` | 开环 PWM 斜坡起停 |
| 16 | [第 38 章](../v5-motion/38-encoder-speed-measurement.md) | 编码器测速 | 10 ms 窗口计数换算 rpm |
| 17 | [第 39 章](../v5-motion/39-speed-closed-loop-pi.md) | 速度闭环 | PI 阶跃响应留档 |
| 18 | [第 40–42 章](../v6-labs-projects/40-lab-method-instruments.md) | 双板记录器 | 交付包五件套——L5 收口 |

逐周自测题不进正文。题面在源章、答案在 [附录 C](../appendix/C-exercises-answers.md)（按合并章号重排）。入门线从第 1 周就动手——第 0 章的开箱流程（见上手卷）在第 1 周之前完成。

十八周只排「动手轨」：47 章里 19 章在表内，28 章不在——[第 0 章](../onramp/00-from-box-to-blink.md) 是第 0 周，v0 前六章（[ch01](../v0-foundations/01-c-memory-model.md) 至 [ch06](../v0-foundations/06-linker-startup-map.md)）是第 1 周之前的预备，其余 21 章（多平台、RTOS 内核后半、交付方法等）用到哪章翻哪章。

想顺着章节线读的人，表内有六处可以顺手回看：这几个动手章的罗盘写着「上一章你手里有…」，而那一位没有周次。先把那一章读了再接本周的动手，衔接更顺；不读也不影响照表做出本周的可展示物——周次绑定的是例程与可展示物，不是阅读顺序。

| 周 | 动手章 | 顺带可回看的上一章 |
| --- | --- | --- |
| 1 | [ch07 构建系统](../v0-foundations/07-build-systems-legacy.md) | [ch06 链接与启动](../v0-foundations/06-linker-startup-map.md) |
| 2 | [ch09 GPIO](../v1-drivers/09-gpio.md) | [ch08 架构、内存与时钟](../v1-drivers/08-architecture-memory-clock.md) |
| 6 | [ch15 ADC/DAC](../v1-drivers/15-adc-dac-sampling.md) | [ch14 DMA](../v1-drivers/14-dma.md) |
| 9 | [ch21 为什么用 RTOS](../v3-rtos/21-why-rtos.md) | [ch20 调试与性能](../v2-reliability/20-debug-performance.md) |
| 13 | [ch35 CAN/USB](../v4-platforms/35-can-usb-fieldbus.md) | [ch34 多核与缓存](../v4-platforms/34-multicore-cache.md) |
| 16 | [ch38 编码器测速](../v5-motion/38-encoder-speed-measurement.md) | [ch37 直流电机开环](../v5-motion/37-dc-motor-openloop.md) |

### 1.1 五阶段能力目标与 47 章依赖索引

三阶段 4/6/8 周继续作为排期示例；下面把同一旅程的能力目标展开为**入门、基础、进阶、项目、深入**，不新增评级，也不替换 L0–L5。分阶段是章节的主要用途，不是五道只能顺次通过的门：第 40 章的安全与取证应在第一次测量前读，第 19 章的恢复纪律应在项目前读，第 46 章现在就可用来排计划。

本表按 `docs/manifest.json` 的 ch00–ch46 与各章罗盘、测量/离开检查逐项对应，共 **47/47 章**，不含六附录。首次主归属数量：入门 **1**、基础 **18**、进阶 **15**、项目 **6**、深入 **7**。数量不表示学习时长或已验证程度。

- **必修**：本书通用闭环的核心知识；已有同等能力者用验收产物自证后可跳读，不要求从 ch01 连续读到 ch46。
- **参考/分支**：按芯片、协议或项目选择；一旦选用该分支，其所列先修就必须满足。没有选电机，不要求为交付记录器先学 PI。
- **必须先会**：理解该行验收任务所需的直接概念依赖；可用已有技能替代读章，不等于此前所有章节必读。条件性依赖在产物栏说明。
- **推荐回看**：帮助解释、测量或排错的阅读顺序，**不构成依赖边**。原罗盘的「上一章」是叙事衔接，不一律当作硬先修。
- 表中产物是读者要完成的任务，**不是本仓库已经实测通过的声明**。没有仪器或板卡时只能完成计算/方案，硬件验收保留待测。

| 章（现行路径） | 主要阶段 / 阅读 | 必须先会（直接依赖） | 推荐回看（非依赖） | 本章留下的验收产物 / 分支条件 |
| --- | --- | --- | --- | --- |
| [ch00 从开箱到点灯：买板、装环境与第一次下载](../onramp/00-from-box-to-blink.md) | 入门 / 必修 | 无章级硬依赖；基础语法/电气安全不足时先补课 | [ch05 工具链与四步构建](../v0-foundations/05-toolchain-four-steps.md)、[ch09 GPIO](../v1-drivers/09-gpio.md)、[ch13 UART 与可恢复帧协议](../v1-drivers/13-uart-framed-protocol.md) | 芯片/供电身份、构建与烧录日志、点灯及首次串口记录 |
| [ch01 嵌入式 C 的内存模型与指针](../v0-foundations/01-c-memory-model.md) | 基础 / 必修 | 无章级硬依赖；基础语法/电气安全不足时先补课 | [ch05 工具链与四步构建](../v0-foundations/05-toolchain-four-steps.md) | 变量段归属、VMA/LMA 与初值来源对照 |
| [ch02 volatile、const 与未定义行为](../v0-foundations/02-c-volatile-ub.md) | 基础 / 必修 | [ch01 嵌入式 C 的内存模型与指针](../v0-foundations/01-c-memory-model.md) | [ch05 工具链与四步构建](../v0-foundations/05-toolchain-four-steps.md) | 同一访存代码的 O0/O2 汇编差异 |
| [ch03 结构体、ABI 与寄存器映射](../v0-foundations/03-struct-abi-registers.md) | 基础 / 必修 | [ch01 嵌入式 C 的内存模型与指针](../v0-foundations/01-c-memory-model.md)、[ch02 volatile、const 与未定义行为](../v0-foundations/02-c-volatile-ub.md) | [ch08 架构、存储器地图与时钟树](../v1-drivers/08-architecture-memory-clock.md) | offsetof/sizeof 与寄存器偏移逐项对账 |
| [ch04 函数指针、状态机与调用约定](../v0-foundations/04-function-pointer-state-machine.md) | 基础 / 必修 | [ch01 嵌入式 C 的内存模型与指针](../v0-foundations/01-c-memory-model.md) | [ch02 volatile、const 与未定义行为](../v0-foundations/02-c-volatile-ub.md) | 状态×事件表及环形缓冲满空规则 |
| [ch05 工具链与四步构建](../v0-foundations/05-toolchain-four-steps.md) | 基础 / 必修 | 无章级硬依赖；基础语法/电气安全不足时先补课 | [ch00 从开箱到点灯：买板、装环境与第一次下载](../onramp/00-from-box-to-blink.md)、[ch01 嵌入式 C 的内存模型与指针](../v0-foundations/01-c-memory-model.md) | 四步构建的 i/s/o/elf 与工具链版本记录 |
| [ch06 链接脚本、启动与 map 体积审计](../v0-foundations/06-linker-startup-map.md) | 基础 / 必修 | [ch01 嵌入式 C 的内存模型与指针](../v0-foundations/01-c-memory-model.md)、[ch05 工具链与四步构建](../v0-foundations/05-toolchain-four-steps.md) | [ch03 结构体、ABI 与寄存器映射](../v0-foundations/03-struct-abi-registers.md) | 向量表、data/bss、map 三条落位证据 |
| [ch07 构建系统与遗留栈](../v0-foundations/07-build-systems-legacy.md) | 基础 / 参考/分支 | [ch05 工具链与四步构建](../v0-foundations/05-toolchain-four-steps.md)、[ch06 链接脚本、启动与 map 体积审计](../v0-foundations/06-linker-startup-map.md) | [ch03 结构体、ABI 与寄存器映射](../v0-foundations/03-struct-abi-registers.md) | 增量构建观察；遗留 SPL 锁定表（选用时） |
| [ch08 架构、存储器地图与时钟树](../v1-drivers/08-architecture-memory-clock.md) | 基础 / 必修 | [ch02 volatile、const 与未定义行为](../v0-foundations/02-c-volatile-ub.md)、[ch03 结构体、ABI 与寄存器映射](../v0-foundations/03-struct-abi-registers.md) | [ch06 链接脚本、启动与 map 体积审计](../v0-foundations/06-linker-startup-map.md) | RCC 回读、总线分频与手算时钟表 |
| [ch09 GPIO](../v1-drivers/09-gpio.md) | 基础 / 必修 | [ch08 架构、存储器地图与时钟树](../v1-drivers/08-architecture-memory-clock.md) | [ch00 从开箱到点灯：买板、装环境与第一次下载](../onramp/00-from-box-to-blink.md)、[ch03 结构体、ABI 与寄存器映射](../v0-foundations/03-struct-abi-registers.md) | 时钟/模式/电平与点灯记录对应 |
| [ch10 中断、NVIC/EXTI、CLIC 与双核](../v1-drivers/10-interrupts-nvic-exti.md) | 基础 / 必修 | [ch04 函数指针、状态机与调用约定](../v0-foundations/04-function-pointer-state-machine.md)、[ch09 GPIO](../v1-drivers/09-gpio.md) | [ch06 链接脚本、启动与 map 体积审计](../v0-foundations/06-linker-startup-map.md) | IRQ 槽位、优先级与清标志的证据 |
| [ch11 SysTick 与时基（含 RTC）](../v1-drivers/11-systick-timebase-rtc.md) | 基础 / 必修 | [ch08 架构、存储器地图与时钟树](../v1-drivers/08-architecture-memory-clock.md)、[ch10 中断、NVIC/EXTI、CLIC 与双核](../v1-drivers/10-interrupts-nvic-exti.md) | [ch09 GPIO](../v1-drivers/09-gpio.md) | LOAD 范围与回绕超时；RTC 按需补读 |
| [ch12 定时器与 PWM](../v1-drivers/12-timers-pwm.md) | 基础 / 必修 | [ch08 架构、存储器地图与时钟树](../v1-drivers/08-architecture-memory-clock.md)、[ch09 GPIO](../v1-drivers/09-gpio.md) | [ch11 SysTick 与时基（含 RTC）](../v1-drivers/11-systick-timebase-rtc.md)、[ch40 实物实验方法与仪器证据](../v6-labs-projects/40-lab-method-instruments.md) | PSC/ARR/CCR 计算与 PWM 波形对账 |
| [ch13 UART 与可恢复帧协议](../v1-drivers/13-uart-framed-protocol.md) | 基础 / 必修 | [ch08 架构、存储器地图与时钟树](../v1-drivers/08-architecture-memory-clock.md)、[ch09 GPIO](../v1-drivers/09-gpio.md) | [ch04 函数指针、状态机与调用约定](../v0-foundations/04-function-pointer-state-machine.md)、[ch40 实物实验方法与仪器证据](../v6-labs-projects/40-lab-method-instruments.md) | BRR、0x55/0x41 位宽与字节日志 |
| [ch14 DMA](../v1-drivers/14-dma.md) | 基础 / 必修 | [ch10 中断、NVIC/EXTI、CLIC 与双核](../v1-drivers/10-interrupts-nvic-exti.md)、[ch13 UART 与可恢复帧协议](../v1-drivers/13-uart-framed-protocol.md) | [ch04 函数指针、状态机与调用约定](../v0-foundations/04-function-pointer-state-machine.md) | USART RX 路线的 NDTR/半区/所有权记录；其他请求源另核映射 |
| [ch15 ADC/DAC 与采样](../v1-drivers/15-adc-dac-sampling.md) | 基础 / 必修 | [ch08 架构、存储器地图与时钟树](../v1-drivers/08-architecture-memory-clock.md)、[ch09 GPIO](../v1-drivers/09-gpio.md) | [ch14 DMA](../v1-drivers/14-dma.md)、[ch40 实物实验方法与仪器证据](../v6-labs-projects/40-lab-method-instruments.md) | VREF/码值/输入电压表；仅扫描 DMA 段另需 ch14 |
| [ch16 I2C 与 SPI](../v1-drivers/16-i2c-spi.md) | 基础 / 必修 | [ch08 架构、存储器地图与时钟树](../v1-drivers/08-architecture-memory-clock.md)、[ch09 GPIO](../v1-drivers/09-gpio.md) | [ch13 UART 与可恢复帧协议](../v1-drivers/13-uart-framed-protocol.md)、[ch40 实物实验方法与仪器证据](../v6-labs-projects/40-lab-method-instruments.md) | I2C 地址/ACK 与 SPI 模式/事务时序各一次对账 |
| [ch17 Flash、IAP 与 OTA](../v1-drivers/17-flash-iap-ota.md) | 基础 / 参考/分支 | [ch06 链接脚本、启动与 map 体积审计](../v0-foundations/06-linker-startup-map.md)、[ch08 架构、存储器地图与时钟树](../v1-drivers/08-architecture-memory-clock.md) | [ch19 看门狗、复位与 HardFault](../v2-reliability/19-watchdog-reset-hardfault.md) | 页/扇区与镜像边界表；升级路线再做恢复设计 |
| [ch18 低功耗设计](../v2-reliability/18-low-power.md) | 深入 / 参考/分支 | [ch08 架构、存储器地图与时钟树](../v1-drivers/08-architecture-memory-clock.md)、[ch11 SysTick 与时基（含 RTC）](../v1-drivers/11-systick-timebase-rtc.md) | [ch13 UART 与可恢复帧协议](../v1-drivers/13-uart-framed-protocol.md)、[ch19 看门狗、复位与 HardFault](../v2-reliability/19-watchdog-reset-hardfault.md) | 唤醒前后时钟、时基、BRR 恢复检查表 |
| [ch19 看门狗、复位与 HardFault](../v2-reliability/19-watchdog-reset-hardfault.md) | 深入 / 必修 | [ch06 链接脚本、启动与 map 体积审计](../v0-foundations/06-linker-startup-map.md)、[ch10 中断、NVIC/EXTI、CLIC 与双核](../v1-drivers/10-interrupts-nvic-exti.md)、[ch11 SysTick 与时基（含 RTC）](../v1-drivers/11-systick-timebase-rtc.md) | [ch20 调试、性能与测量](../v2-reliability/20-debug-performance.md) | 看门狗最坏超时预算与复位/HardFault 现场记录方案 |
| [ch20 调试、性能与测量](../v2-reliability/20-debug-performance.md) | 深入 / 必修 | [ch05 工具链与四步构建](../v0-foundations/05-toolchain-four-steps.md)、[ch06 链接脚本、启动与 map 体积审计](../v0-foundations/06-linker-startup-map.md)、[ch08 架构、存储器地图与时钟树](../v1-drivers/08-architecture-memory-clock.md) | [ch10 中断、NVIC/EXTI、CLIC 与双核](../v1-drivers/10-interrupts-nvic-exti.md)、[ch19 看门狗、复位与 HardFault](../v2-reliability/19-watchdog-reset-hardfault.md) | 调试链分层、断点失败分诊及性能测量开销说明 |
| [ch21 为什么需要 RTOS](../v3-rtos/21-why-rtos.md) | 进阶 / 必修 | [ch04 函数指针、状态机与调用约定](../v0-foundations/04-function-pointer-state-machine.md)、[ch10 中断、NVIC/EXTI、CLIC 与双核](../v1-drivers/10-interrupts-nvic-exti.md)、[ch11 SysTick 与时基（含 RTC）](../v1-drivers/11-systick-timebase-rtc.md) | [ch20 调试、性能与测量](../v2-reliability/20-debug-performance.md) | 裸机响应上界与任务/中断优先级、RAM 预算表 |
| [ch22 任务、TCB 与调度](../v3-rtos/22-tasks-tcb-scheduler.md) | 进阶 / 必修 | [ch21 为什么需要 RTOS](../v3-rtos/21-why-rtos.md) | [ch04 函数指针、状态机与调用约定](../v0-foundations/04-function-pointer-state-machine.md) | 任务状态转换、优先级与调度轨迹 |
| [ch23 上下文切换与移植](../v3-rtos/23-context-switch-porting.md) | 进阶 / 参考/分支 | [ch06 链接脚本、启动与 map 体积审计](../v0-foundations/06-linker-startup-map.md)、[ch10 中断、NVIC/EXTI、CLIC 与双核](../v1-drivers/10-interrupts-nvic-exti.md)、[ch22 任务、TCB 与调度](../v3-rtos/22-tasks-tcb-scheduler.md) | [ch04 函数指针、状态机与调用约定](../v0-foundations/04-function-pointer-state-machine.md) | 栈现场、三个异常与向量名逐项对照 |
| [ch24 队列、信号量与通知](../v3-rtos/24-queue-semaphore-notification.md) | 进阶 / 必修 | [ch04 函数指针、状态机与调用约定](../v0-foundations/04-function-pointer-state-machine.md)、[ch22 任务、TCB 与调度](../v3-rtos/22-tasks-tcb-scheduler.md) | [ch14 DMA](../v1-drivers/14-dma.md) | 队列/信号量/通知选型、FromISR 与资源归属表 |
| [ch25 内存管理](../v3-rtos/25-memory-management.md) | 进阶 / 必修 | [ch01 嵌入式 C 的内存模型与指针](../v0-foundations/01-c-memory-model.md)、[ch22 任务、TCB 与调度](../v3-rtos/22-tasks-tcb-scheduler.md) | [ch06 链接脚本、启动与 map 体积审计](../v0-foundations/06-linker-startup-map.md) | heap 选择、块头开销与历史最低水位解释 |
| [ch26 设备框架、shell 与配置系统](../v3-rtos/26-device-framework-shell.md) | 进阶 / 参考/分支 | [ch04 函数指针、状态机与调用约定](../v0-foundations/04-function-pointer-state-machine.md)、[ch13 UART 与可恢复帧协议](../v1-drivers/13-uart-framed-protocol.md)、[ch22 任务、TCB 与调度](../v3-rtos/22-tasks-tcb-scheduler.md) | [ch24 队列、信号量与通知](../v3-rtos/24-queue-semaphore-notification.md) | 设备 open/ref_count 与 Shell 命令调用链 |
| [ch27 双 OS 对照与选型](../v3-rtos/27-rtos-comparison-selection.md) | 进阶 / 参考/分支 | [ch24 队列、信号量与通知](../v3-rtos/24-queue-semaphore-notification.md)、[ch25 内存管理](../v3-rtos/25-memory-management.md) | [ch26 设备框架、shell 与配置系统](../v3-rtos/26-device-framework-shell.md) | 带栈单位、tick 位宽、内存证据的 RTOS 取舍表 |
| [ch28 芯片迁移方法论与引脚/外设差异](../v4-platforms/28-chip-migration-differences.md) | 进阶 / 参考/分支 | [ch06 链接脚本、启动与 map 体积审计](../v0-foundations/06-linker-startup-map.md)、[ch08 架构、存储器地图与时钟树](../v1-drivers/08-architecture-memory-clock.md)、[ch09 GPIO](../v1-drivers/09-gpio.md) | [ch17 Flash、IAP 与 OTA](../v1-drivers/17-flash-iap-ota.md) | 芯片/封装/引脚/BOOT/时钟迁移清单 |
| [ch29 GD32 系列对照（ARM + RISC-V）](../v4-platforms/29-gd32-arm-riscv.md) | 进阶 / 参考/分支 | [ch28 芯片迁移方法论与引脚/外设差异](../v4-platforms/28-chip-migration-differences.md) | [ch07 构建系统与遗留栈](../v0-foundations/07-build-systems-legacy.md) | ARM/RISC-V 差异与 GD32 时钟/USB 预算复算 |
| [ch30 ESP32-S3 架构、启动与工程](../v4-platforms/30-esp32s3-architecture-boot.md) | 进阶 / 参考/分支 | [ch05 工具链与四步构建](../v0-foundations/05-toolchain-four-steps.md)、[ch06 链接脚本、启动与 map 体积审计](../v0-foundations/06-linker-startup-map.md) | [ch28 芯片迁移方法论与引脚/外设差异](../v4-platforms/28-chip-migration-differences.md) | ESP32-S3 日志三次交接与分区表解释 |
| [ch31 ESP32 外设、驱动框架与音频链路](../v4-platforms/31-esp32-drivers-audio.md) | 进阶 / 参考/分支 | [ch30 ESP32-S3 架构、启动与工程](../v4-platforms/30-esp32s3-architecture-boot.md) | [ch13 UART 与可恢复帧协议](../v1-drivers/13-uart-framed-protocol.md)、[ch16 I2C 与 SPI](../v1-drivers/16-i2c-spi.md) | S3 焊盘能力/占用核对；UART/I2C/SPI 数据归属 |
| [ch32 Wi-Fi、蓝牙与 ESP-NOW](../v4-platforms/32-esp32-wifi-ble-espnow.md) | 进阶 / 参考/分支 | [ch30 ESP32-S3 架构、启动与工程](../v4-platforms/30-esp32s3-architecture-boot.md)、[ch31 ESP32 外设、驱动框架与音频链路](../v4-platforms/31-esp32-drivers-audio.md) | [ch04 函数指针、状态机与调用约定](../v0-foundations/04-function-pointer-state-machine.md)、[ch24 队列、信号量与通知](../v3-rtos/24-queue-semaphore-notification.md) | Wi-Fi 状态机、退避与失败 reason 分诊表 |
| [ch33 网络与协议栈](../v4-platforms/33-network-protocol-stack.md) | 进阶 / 参考/分支 | [ch13 UART 与可恢复帧协议](../v1-drivers/13-uart-framed-protocol.md)、[ch14 DMA](../v1-drivers/14-dma.md) | [ch24 队列、信号量与通知](../v3-rtos/24-queue-semaphore-notification.md)、[ch32 Wi-Fi、蓝牙与 ESP-NOW](../v4-platforms/32-esp32-wifi-ble-espnow.md)、[ch34 多核、Cache 与内存一致性](../v4-platforms/34-multicore-cache.md) | 选定一条网络路径，画 DMA 内存/线程归属及恢复链；缓存段另读 ch34 |
| [ch34 多核、Cache 与内存一致性](../v4-platforms/34-multicore-cache.md) | 进阶 / 参考/分支 | [ch02 volatile、const 与未定义行为](../v0-foundations/02-c-volatile-ub.md)、[ch14 DMA](../v1-drivers/14-dma.md) | [ch10 中断、NVIC/EXTI、CLIC 与双核](../v1-drivers/10-interrupts-nvic-exti.md)、[ch30 ESP32-S3 架构、启动与工程](../v4-platforms/30-esp32s3-architecture-boot.md) | Cache/DMA clean/invalidate 方向与对齐表；S3 分支需 ch30 |
| [ch35 现场总线与 USB](../v4-platforms/35-can-usb-fieldbus.md) | 进阶 / 参考/分支 | [ch08 架构、存储器地图与时钟树](../v1-drivers/08-architecture-memory-clock.md)、[ch09 GPIO](../v1-drivers/09-gpio.md)、[ch10 中断、NVIC/EXTI、CLIC 与双核](../v1-drivers/10-interrupts-nvic-exti.md) | [ch13 UART 与可恢复帧协议](../v1-drivers/13-uart-framed-protocol.md)、[ch14 DMA](../v1-drivers/14-dma.md) | CAN 位时序整除/采样点或 USB 端点/缓冲归属，按所选分支验收 |
| [ch36 电机驱动与供电](../v5-motion/36-motor-driver-power.md) | 项目 / 参考/分支 | [ch09 GPIO](../v1-drivers/09-gpio.md)、[ch12 定时器与 PWM](../v1-drivers/12-timers-pwm.md) | [ch19 看门狗、复位与 HardFault](../v2-reliability/19-watchdog-reset-hardfault.md) | 控制/动力电流分层与上电/复位/故障关闭检查表 |
| [ch37 直流电机开环调速](../v5-motion/37-dc-motor-openloop.md) | 项目 / 参考/分支 | [ch12 定时器与 PWM](../v1-drivers/12-timers-pwm.md)、[ch36 电机驱动与供电](../v5-motion/36-motor-driver-power.md) | [ch11 SysTick 与时基（含 RTC）](../v1-drivers/11-systick-timebase-rtc.md)、[ch19 看门狗、复位与 HardFault](../v2-reliability/19-watchdog-reset-hardfault.md) | 开环斜坡、双限幅、租约与换向时序方案 |
| [ch38 编码器与转速测量](../v5-motion/38-encoder-speed-measurement.md) | 项目 / 参考/分支 | [ch10 中断、NVIC/EXTI、CLIC 与双核](../v1-drivers/10-interrupts-nvic-exti.md)、[ch12 定时器与 PWM](../v1-drivers/12-timers-pwm.md) | [ch37 直流电机开环调速](../v5-motion/37-dc-motor-openloop.md) | P×Q×G 口径、计数差与 rpm/量化下限复算 |
| [ch39 速度闭环与 PI](../v5-motion/39-speed-closed-loop-pi.md) | 项目 / 参考/分支 | [ch04 函数指针、状态机与调用约定](../v0-foundations/04-function-pointer-state-machine.md)、[ch13 UART 与可恢复帧协议](../v1-drivers/13-uart-framed-protocol.md)、[ch19 看门狗、复位与 HardFault](../v2-reliability/19-watchdog-reset-hardfault.md)、[ch37 直流电机开环调速](../v5-motion/37-dc-motor-openloop.md)、[ch38 编码器与转速测量](../v5-motion/38-encoder-speed-measurement.md) | [ch24 队列、信号量与通知](../v3-rtos/24-queue-semaphore-notification.md) | PI 单步手算、五态恢复链与阶跃四指标验收方案 |
| [ch40 实物实验方法与仪器证据](../v6-labs-projects/40-lab-method-instruments.md) | 基础 / 必修 | 无章级硬依赖；基础语法/电气安全不足时先补课 | [ch00 从开箱到点灯：买板、装环境与第一次下载](../onramp/00-from-box-to-blink.md)、[ch09 GPIO](../v1-drivers/09-gpio.md)、[ch12 定时器与 PWM](../v1-drivers/12-timers-pwm.md)、[ch13 UART 与可恢复帧协议](../v1-drivers/13-uart-framed-protocol.md) | 押注→测量→对账→登记；仪器安全先读，不等到第40章才量 |
| [ch41 双板综合项目](../v6-labs-projects/41-dual-board-logger-project.md) | 项目 / 参考/分支 | [ch04 函数指针、状态机与调用约定](../v0-foundations/04-function-pointer-state-machine.md)、[ch13 UART 与可恢复帧协议](../v1-drivers/13-uart-framed-protocol.md)、[ch17 Flash、IAP 与 OTA](../v1-drivers/17-flash-iap-ota.md)、[ch19 看门狗、复位与 HardFault](../v2-reliability/19-watchdog-reset-hardfault.md) | [ch14 DMA](../v1-drivers/14-dma.md)、[ch15 ADC/DAC 与采样](../v1-drivers/15-adc-dac-sampling.md)、[ch24 队列、信号量与通知](../v3-rtos/24-queue-semaphore-notification.md)、[ch40 实物实验方法与仪器证据](../v6-labs-projects/40-lab-method-instruments.md) | 双板 port 边界、载荷/队列/期限预算与故障注入计划 |
| [ch42 项目实战与交付验收](../v6-labs-projects/42-project-delivery-acceptance.md) | 项目 / 必修 | [ch40 实物实验方法与仪器证据](../v6-labs-projects/40-lab-method-instruments.md) | [ch19 看门狗、复位与 HardFault](../v2-reliability/19-watchdog-reset-hardfault.md)、[ch41 双板综合项目](../v6-labs-projects/41-dual-board-logger-project.md) | 所选项目四问、六预算及五件套；实现先修取决于项目，不强制 ch41 |
| [ch43 AI 结对开发与提示词工作流](../v7-delivery/43-ai-pair-programming.md) | 深入 / 参考/分支 | 无章级硬依赖；基础语法/电气安全不足时先补课 | [ch05 工具链与四步构建](../v0-foundations/05-toolchain-four-steps.md)、[ch42 项目实战与交付验收](../v6-labs-projects/42-project-delivery-acceptance.md)、[ch44 手册对账与幻觉防御](../v7-delivery/44-manual-reconciliation-hallucination.md) | 三段式工单、模型权限四问与人工签字边界 |
| [ch44 手册对账与幻觉防御](../v7-delivery/44-manual-reconciliation-hallucination.md) | 深入 / 必修 | 无章级硬依赖；基础语法/电气安全不足时先补课 | [ch03 结构体、ABI 与寄存器映射](../v0-foundations/03-struct-abi-registers.md)、[ch08 架构、存储器地图与时钟树](../v1-drivers/08-architecture-memory-clock.md)、[ch40 实物实验方法与仪器证据](../v6-labs-projects/40-lab-method-instruments.md)、[ch43 AI 结对开发与提示词工作流](../v7-delivery/43-ai-pair-programming.md) | 一条主张的手册/源码/板卡/测量核对卡；读回和波形分析回相应基础章 |
| [ch45 常见故障排查手册](../v7-delivery/45-troubleshooting-handbook.md) | 深入 / 必修 | 无章级硬依赖；基础语法/电气安全不足时先补课 | [ch09 GPIO](../v1-drivers/09-gpio.md)、[ch13 UART 与可恢复帧协议](../v1-drivers/13-uart-framed-protocol.md)、[ch19 看门狗、复位与 HardFault](../v2-reliability/19-watchdog-reset-hardfault.md)、[ch20 调试、性能与测量](../v2-reliability/20-debug-performance.md) | 从一条症状走到区分证据与下一动作，不必先通读44章 |
| [ch46 资料、学习路线与开源地图](../v7-delivery/46-resources-roadmap-open-source.md) | 深入 / 必修 | 无章级硬依赖；基础语法/电气安全不足时先补课 | [ch00 从开箱到点灯：买板、装环境与第一次下载](../onramp/00-from-box-to-blink.md)、[ch42 项目实战与交付验收](../v6-labs-projects/42-project-delivery-acceptance.md)、[ch44 手册对账与幻觉防御](../v7-delivery/44-manual-reconciliation-hallucination.md) | 个人计划、L0–L5 自评及下一份缺口证据 |

#### 阶段验收：按证据放行，不按读完多少章放行

| 能力目标 | 可执行动作与通过判据 | 失败后复习路径 | 与原证据级别的关系 |
| --- | --- | --- | --- |
| 入门：独立装环境、构建、烧录、点灯、串口 | 按 ch00 完成环境版本记录；保存自己构建与校验烧录日志，冷复位后观察点灯；按 UART 样板发一个字节并保存回显。任一项缺日志、板型身份或现象记录均未过；只会运行预编译文件不算独立构建 | 工具找错回 ch05；不启动回 ch06/ch08；灯和串口分别走下述样板，不把 F103/F407 混接 | L0；时序精度在基础阶段再验 |
| 基础：GPIO/中断/定时器/ADC/DMA，能测量与排错 | 点灯、PWM、UART 三协议各留一份记录；中断另存源/使能/清标志与事件计数；ADC 用安全范围内两档已记录输入电压对照 VREF/码值；DMA 记录长度、NDTR 与边界消费。每项须有理论、原始证据、偏差、下一排错动作，不能用源码代替波形 | 时钟不符回 ch08；时基回 ch10–12；乱码回 ch13；长度/归属回 ch14；采样偏差回 ch15；仪器设置回 ch40 | L1–L2；未做 ADC/DMA 不能用三样板替代全部基础验收 |
| 进阶：通信并发与资源归属 | 选 RTOS 或裸机并发路径，画一条收发数据流，标生产者/消费者、ISR/任务、缓冲所有权、阻塞上界与溢出/恢复策略；用短包、跨边界、积压三种输入留计数和字节比对。只写「加锁」或无丢弃规则不通过；多平台/网络按所选分支增加内存与恢复证据 | 状态机回 ch04；中断优先级回 ch10/ch21；队列/通知回 ch24；内存水位回 ch25；选 Cache/DMA 分支再回 ch34 | L2→L4 中的数据/系统部分；不跳过 L3 的可靠性证据 |
| 项目：交付可重建、可验收的小系统 | 从 ch41 双板或 ch36–39 运动线选择一个，也可用自己的小系统；按 ch42 四问写阈值和测法、填六预算，提交五件套。由第二人或按干净环境说明重建，执行正常与至少一个失败/恢复用例，记录结果；草图、空验收表不算交付 | 缺可重建材料回 ch05–07；边界不清回 ch41；预算或验收空泛回 ch42；恢复不明回 ch19 | L5 的交付形式，仍需所选功能的 L1–L4 证据支撑 |
| 深入：手册勘误、预算、性能、恢复与方案取舍 | 选一条有争议主张，按 ch44 列手册版本/芯片与板卡/源码/测量四证；按 ch20 说明计时开销和最坏情况，按 ch18/ch19 写恢复步骤；比较两方案的资源预算与失败代价。无实测则标未验证，不能据此宣布性能达标 | 主张来源回附录 E；性能测法回 ch20/ch40；故障现场回 ch19/ch45；重新用 ch46 自评下一缺口 | 复核 L3–L5，不新增 L6，不凭章数授予「精通」 |

复习从**失败信号**开始：先查 [ch45](./45-troubleshooting-handbook.md) 的分诊表，再沿本表「必须先会」反向补缺；补完重做失败用例，不把整本重读当唯一办法。上述依赖不含「推荐回看」边，允许 ch00→ch09/ch13 的实践先行，再按计算/排错需要补语言和构建。

三个第一轮取证入口见 [附录B](../appendix/B-project-index.md) 的基础取证协议表：仓库路径分别为 `labs/gpio-blink/README.md`、`labs/timer-pwm/README.md`、`labs/uart-dma/README.md`，共用 `labs/README.md` 的安全与证据记录。它们复用 ch09 E01、ch12 E03、ch13 E02 的方法，不另编实验编号，F407 主线与 F103 对照分开。

### 2. 前置知识五块的「够用」标准

| 块 | 必须会 | 够用即可 | 补课信号 |
| --- | --- | --- | --- |
| C 语言 | 指针/位运算/struct | 函数指针/链接过程 | 看到 `*p++` 发怵 |
| 数字电路 | 电平/上拉下拉 | 时序图 | 分不清推挽开漏 |
| 模拟电路 | 欧姆定律/分压 | 运放常识 | 不敢分压采样 |
| 计组 | 内存映射概念 | 流水线/缓存 | 不知道寄存器是内存 |
| 英语 | 查词典读手册 | 通读 | 手册一页没读过 |

「够用即可」是主流。嵌入式入门最大的坑是把 C 语言学完才敢点灯。

### 3. L0–L5 能力级别与卷章映射

三阶段表回答「这周做什么」，L0–L5 回答「现在能拿出什么证据」。级别按证据划分，不按读完的章数划分。合并版八卷按下面的方式归档；卷 0→卷 7 是默认叙事顺序，按能力跳读与条件先修见上表。

| 级别 | 能做什么 | 对应卷/章 | 过关证据 | 下一级还缺什么 |
| --- | --- | --- | --- | --- |
| L0 起步 | 独立编译、烧录、复位；说清芯片、引脚、电源、时钟边界 | 卷 0；第 8–9 章 | 构建日志、烧录记录、复位后的最小可见结果、版本记录 | 一只脚的真实电平与波形 |
| L1 驱动 | 用 GPIO、中断、时基、定时器/PWM 驱动真实外设 | 第 9–12 章 | 波形、寄存器读回、可见结果三者一致 | 字节怎么进出，缓冲区归谁 |
| L2 数据 | 把 UART、SPI、I2C、ADC/DAC、DMA、Flash 的数据路径讲清 | 第 13–17 章；附录 A | 时序图、缓冲区状态、代码路径能对上 | 失败能否复现，原因能否区分 |
| L3 可靠 | 处理掉电、升级、看门狗、低功耗与崩溃现场 | 卷 2 | 失败复现记录、复位/唤醒/保护现场的证据 | 任务、资源与截止时间能否预算 |
| L4 系统 | 在 RTOS、迁移、网络、Cache、运动控制里做取舍 | 卷 3–5 | 边界、最坏情况、恢复路径、取舍理由 | 一份别人能重建、验收、交接的交付包 |
| L5 交付 | 把项目做成可重建、可验收、可交接的交付包 | 卷 6–7 | 交付五件套、验收记录、资料与开源引用 | 终点：能对别人的系统做同样的证据审查 |

L0 与 L1 都引用第 9 章：L0 只要求点灯闭环，L1 要求中断、定时器/PWM 的波形证据。级别按证据算，不按章号算。

卷 3–5 的正文在卷 6 之前。按能力归档时，它们属于 L4；读到卷 6–7 时，用交付包把 L4 的边界证据收口。

![手绘板：L0–L5 六级能力与过关证据，按合并版八卷归档（原理示意，非实拍）](/images/ch46-l0-l5-ladder.png)

## 机制

### 一、三种开发方式与统一口径

六维对比（寄存器/SPL/HAL+LL+CubeMX）：效率、可移植性、学习曲线、社区资料、维护状态、适用阶段。

**SPL 已停止维护**（[卷 0 第 7 章](../v0-foundations/07-build-systems-legacy.md) 同口径）。两书建议相反：D00 建议「HAL 入门→寄存器对照→LL 优化」，mbF 建议「顺序是寄存器→库」。

**全书的统一口径：寄存器打底（最小验证矩阵那几行）+ HAL 做产品**。寄存器打底的理由是排错时不黑盒（[v1 第 9 章](../v1-drivers/09-gpio.md) 的寄存器版与 HAL 版对照实验已经教了这一课），HAL 做产品的理由是生态与移植；取舍声明写在这里，后文不再摇摆。

### 二、手册六类与三步法

| 前缀 | 全称 | 查什么 |
| --- | --- | --- |
| RM | Reference Manual | 寄存器/位段/时序 |
| DS | Datasheet | 电气参数/引脚/封装 |
| PM | Programming Manual | 指令集/内核（PM0056=CM3） |
| AN | Application Note | 某主题的做法（AN4891=H7 架构） |
| UM | User Manual | 工具/固件库用法 |
| ES | Errata Sheet | 已知勘误 |

查手册三步法：①定手册（RM 寄存器/DS 电气/AN 做法）→ ②Ctrl+F 搜寄存器名或位名 → ③读功能描述章的时序与公式。三个检索示例：TIM1 占空比（RM0008 的 CCR1 段）、PA11 的 USB 复用（DS5319 表 5）、F4 DMA 的 FIFO（AN4031 + RM0090，F1 DMAF1 DMA 无 FIFO/突发，F4 有，[v1 第 14 章](../v1-drivers/14-dma.md) 口径）。记忆口诀：**R 看寄存器、D 看数据、A 看应用、U 看工具、E 看坑**。

![学习路线三阶段与三道门槛（原理示意）](/figures/sample-00-roadmap-gates.svg)

![手绘板：三条学习路径与 API 三 lanes 对照（原理示意，非实拍）](/images/ch00-three-api-lanes.png)

### 三、采购清单：两条线并陈

| 线 | 装备 | 预算（估算区间，以当日为准） |
| --- | --- | --- |
| F103 BluePill 起步线 | BluePill 15~30 + ST-Link 克隆 15~40 + 面包板 8~20 + 杜邦线 8~15 | 极简约 60 元；全套约 200~300 元 |
| F407/ESP32-S3 实战线 | 野火 F407 霸天虎 + 立创实战派 S3（板载 QMI8658/音频/屏） | 按 mbF 装备清单口径（[第 31 章](../v4-platforms/31-esp32-drivers-audio.md) 板级事实） |

价格全部是区间加自注。不是事实数。仪器选型两表（硬件 7 行：调试器/逻辑分析仪/示波器/串口/万用表/功耗计/焊接；软件 11 行：CubeMX/CubeIDE/Keil/IAR/PlatformIO/CLion/VS Code/OpenOCD/KiCad/CubeMonitor/PulseView）预算区间同口径，软件定位与 [v1 第 5 章](../v0-foundations/05-toolchain-four-steps.md)、[卷 0 第 7 章](../v0-foundations/07-build-systems-legacy.md)、[v1 第 20 章](../v2-reliability/20-debug-performance.md) 一致。

### 四、构建合同与命令组（索引）

四个 IDE 入口汇入同一 CMake preset 的构建合同、OpenOCD 烧录/GDB 六步、PlatformIO 配置、CubeProgrammer 的 RDP 警告（**RDP=0xAA 解保护会整片擦除**）。技术正文归 [v1 第 5 章](../v0-foundations/05-toolchain-four-steps.md)、[卷 0 第 7 章](../v0-foundations/07-build-systems-legacy.md)、[v1 第 20 章](../v2-reliability/20-debug-performance.md)，这里不重复命令块。

### 五、开源：怎么选、怎么读、怎么问

- **怎么选**：维护活跃度（最近 commit）、license（五族口径见 附录 F）、社区（issue 响应）、与你的芯片匹配（port 层存在性）。
- **怎么读**：先读 README 的「编译一条命令」、再读目录结构、再读一个最小例程。**归档 vs 镜像**要分清（mirror 不含 issue 讨论）。
- **怎么问**：提问五件事：版本三元组（SDK/内核 commit/工具链）、最小复现、预期 vs 实际、完整日志、你已经试过什么。
- **入口仓库一行表**：FreeRTOS-Kernel、RT-Thread、libopencm3、STM32CubeF4、esp-idf、lwIP、OpenOCD 七个的全量表在[附录 F](../appendix/F-open-source-community-map.md)（2026-10-26 快照，附九个知识点）；Mbed TLS 与 KiCad 不在 F 的仓库地图——前者在本书只以 CubeH7 子模块出现（[第 33 章](../v4-platforms/33-network-protocol-stack.md)），后者是工具，都不是有对应章的仓库地图对象，星标见本章上表（2026-11-15）。

#### 社区开源书、课程与配套代码

社区资源先分四类，再谈读哪一本。书、课、配套代码和社区文章的许可与证据边界不同，混成一类最容易把示例代码直接搬进产品。表里按四组排：开源书、开源课程、配套代码、社区文集/片段；同一组内的许可可能不同，逐行看。

| 类型 | 仓库（星标） | 许可（仓库根） | 怎么用 | 边界 |
| --- | --- | --- | --- | --- |
| 开源书/指南 | `cpq/bare-metal-programming-guide`（5010） | MIT | 从零写裸机：启动、寄存器、链接脚本一条线 | 不是 STM32 手册；地址、时钟、位段回 RM/DS |
| 开源书（Rust 路线） | `rust-embedded/book`（1358）、`rust-embedded/discovery`（1606） | 代码 MIT/Apache-2.0；正文 CC BY-SA 4.0（book）/ CC BY 4.0（discovery） | 用另一门语言对照内存映射、所有权与外设抽象 | 当前 Discovery 主版本用 micro:bit v2；F3 discovery 版已标为 deprecated，换板要重查外设 |
| 开源课程 | `microsoft/IoT-For-Beginners`（17191） | MIT | 12 周 24 课的 IoT 全链路，补云、设备与数据视角 | 课程作业不是产品验收；硬件与云服务按当前版本重核 |
| 开源课程/实验 | `jserv/mini-arm-os`（1264） | BSD-2-Clause（`LICENSE` 原文；GitHub 识别为 NOASSERTION） | 从上下文切换写到多任务，补 RTOS 的从零那一层 | 教学内核不是产品 RTOS；仿真实验不等于板级验收 |
| 书的配套代码 | `cnoviello/mastering-stm32`（496） | GPL-3.0 | 对照《Mastering STM32》的例程读 HAL | 仓库只放例程，书正文不在仓库；GPL-3.0 代码不要直接链进闭源固件 |
| 社区文集 | `memfault/interrupt`（560） | CC BY-SA 4.0（`license.md` 原文；GitHub 识别为 NOASSERTION） | 读排错、固件更新、可观测性等工程文章 | 文章不是手册；引用要带版本与日期 |
| 代码片段 | `nkolban/esp32-snippets`（2521） | Apache-2.0 | 查 ESP32 外设与协议片段 | 片段不是完整工程；最后更新 2024，先对当前 IDF 版本 |

星标取 2026-11-15 的 GitHub API 返回值，和[附录 F](../appendix/F-open-source-community-map.md) 的 2026-10-26 仓库快照不同日；只用来看量级，不作排名。许可以仓库根文件原文为准；GitHub 的 `NOASSERTION` 只表示它没有识别出标准族，不代表没有许可。

三条读法：

1. **先跑最小例程，再读讲解。** 跑不起来先对工具链、板型和版本，不要先改讲解里的寄存器值。
2. **书里的地址、时钟、位段回对应 RM/DS 复核。** 书可以帮你找路径，判据仍在手册和测量。
3. **许可按仓库根文件读。** MIT/Apache-2.0 可以进闭源固件（保留版权与许可声明，Apache-2.0 若有 `NOTICE` 也一并保留）；GPL-3.0 不要直接链进闭源固件；CC BY-SA 4.0 的文章转载要署名并以相同方式共享。配套代码的许可和书的许可分开看。

![手绘板：社区开源书、课程、配套代码与社区文章四类资源的读法与许可边界（原理示意，非实拍）](/images/ch46-oss-four-lanes.png)

开源库七行对比（HAL/LL、SPL V3.5.0、libopencm3、ChibiOS、Zephyr、RT-Thread、FreeRTOS）的定位描述沿用 D20 表；版本细节带 附录 F 的证据口径。

### 六、生态计数口径（重申）

[第 27 章](../v3-rtos/27-rtos-comparison-selection.md) 立的规则在这里再明确一次：**数量类陈述（软件包数百个、仓库数千个、用户数）必须带抓取日期与来源，否则不写**。正文与附录 F 的全部星标/计数已带日期；你写文档时同样执行。

## 测量与证据

| 结论 | 身份 | 判据 |
| --- | --- | --- |
| 三阶段 4/6/8 周 | 文档推导（计划表） | D00:163-201 计数自洽 |
| 前置知识五块表 | 文档推导（教学标定） | D00:109-117 |
| L0–L5 级别与卷章映射 | 文档推导（教学标定） | 与 CONTENT_GUIDE 的 L0–L5 口径一致；每级都有证据与下一级缺口 |
| 社区书/课/文集/片段星标 | 来源说法（GitHub API，2026-11-15） | 8 个仓库当日复核；和 附录 F 的 2026-10-26 快照不同日 |
| 开源书/课程许可 | 来源原文（仓库根许可文件） | MIT/Apache-2.0/BSD-2-Clause/GPL-3.0/CC BY-SA 4.0/CC BY 4.0 逐仓读原文 |
| 采购价格区间 | 来源说法 | 自注「以当日价格为准」 |
| SPL 停更 | 手册级 | 与 [卷 0 第 7 章](../v0-foundations/07-build-systems-legacy.md) 一致 |
| 手册六类命名 | 手册级 | ST 文档体系（修正源章「五种」内部不一致） |
| 查手册三步法三示例 | 手册级 | 检索路径可复现 |
| 开源库七行对比 | 手册级（定位） | 版本细节归 附录 F |
| 工具选型价格 | 来源说法待核 | 区间估算 |
| 星标/生态计数 | 来源说法（带日期 2026-10-26） | 附录 F 双源同日核对 |

## 失败分支

| 症状 | 第一条假设 | 区分实验 |
| --- | --- | --- |
| 学了两周还没点灯 | 路线跳步或装备不全 | 对三阶段表；采购清单核对 |
| 读完一章仍不知道自己在哪一级 | 只按章数推进，没有对照证据 | 用 L0–L5 表写「能拿出什么」，缺哪份证据就回对应卷 |
| 开源书跑不起来 | 工具链/板型/版本与书不同 | 先对版本三元组和板型；再跑书里的最小例程 |
| 想把配套代码直接搬进产品 | 没看仓库根许可 | 先读 `LICENSE`/`COPYING`；GPL-3.0 与 CC BY-SA 的义务分开处理 |
| 手册查不到位段 | 前缀选错（RM/DS 分工） | 六类表重对；三步法走一遍 |
| 开源库选型纠结 | 没先写需求四问（[第 42 章](../v6-labs-projects/42-project-delivery-acceptance.md)） | 四问先行；license 五族过一遍 |
| 提问没人回 | 缺版本三元组或最小复现 | 提问五件事重填 |
| 引用生态数字被质疑 | 没带抓取日期 | 补日期与来源，或删除 |
| 两书建议冲突无所适从 | 没看到这里的统一口径声明 | 寄存器打底 + HAL 产品；理由在这里 |

## 离开检查

- 三阶段表能填出自己的计划与过关判据。
- 能指出自己停在 L0–L5 哪一级，并写出下一级缺的证据。
- 前置知识五块自评完成，「够用即可」不焦虑。
- 统一口径（寄存器打底 + HAL 做产品）能说出取舍理由。
- 手册六类与三步法能当场查到一个位段。
- 能从四类社区资源里选一本开源书或课程，说明它的许可边界和不能替代什么。
- 两条采购线能列；价格全部是区间加自注。
- 提问五件事与生态计数口径执行到位。

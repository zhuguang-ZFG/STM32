---
title: "从开箱到点灯：买板、装环境与第一次下载"
platforms: [generic]
---

# 从开箱到点灯：买板、装环境与第一次下载

这一章在所有理论之前。它回答三件事：这块芯片是什么、你要买什么、怎么让第一颗灯在**你的**板子上亮起来。全书的 46 章按知识分层组织（语言与构建 → 驱动 → 可靠性 → RTOS → 多平台 → 运动 → 项目 → 交付），本章是唯一不按分层走的一章：它按「你的准备周（第 0 周）」组织，先跑通构建、烧录与点灯的最小闭环，再接上[第 46 章](../v7-delivery/46-resources-roadmap-open-source.md)的十八周排期——第 1 周从构建系统开始。读完本章，你手里应该有三样东西——构建日志、烧录记录、一块按你的指令闪烁的板子；这正是 [L0 级别](../v7-delivery/46-resources-roadmap-open-source.md)要求的过关证据。

## 本章罗盘

- **问题**：入门的第一周做什么——买哪块板、装哪个工具链、第一次构建与烧录各会卡在哪？「点灯」为什么值得认真做一次，而不是抄一段代码了事？
- **交付**：完成一次从源码到闪烁的完整闭环，并留下 L0 要求的三样证据；遇到「灯不闪」时能按三条失败分支分诊；能用串口跟芯片完成第一次对话。
- **级别**：L0 起步。证据位置：「你应该看到」各清单与[第 40 章](../v6-labs-projects/40-lab-method-instruments.md) 的记录表；读完留下构建日志、烧录记录与一张填写过的记录表。
- **开源读法**：本章的例程是 `examples/gpio-blink` 与 `examples/uart-dma-idle`（[附录 B](../appendix/B-project-index.md) 登记），README 里有完整接线与命令；工具链事实仍回[第 5 章](../v0-foundations/05-toolchain-four-steps.md)。
- **边界**：本章只做「跑起来」，不解释机制——GPIO 的寄存器语义在[第 9 章](../v1-drivers/09-gpio.md)，时钟树在[第 8 章](../v1-drivers/08-architecture-memory-clock.md)，串口在[第 13 章](../v1-drivers/13-uart-framed-protocol.md)；本章出现的数字（115200、BRR `0x271`、1 Hz）全部转引已冻结口径，不新造。
- **依据锚点**：点灯的 1 Hz、串口的 115200 与 BRR `0x271` 转引[第 7 章](../v0-foundations/07-build-systems-legacy.md)、[第 9 章](../v1-drivers/09-gpio.md)、[第 13 章](../v1-drivers/13-uart-framed-protocol.md)已冻结口径；PC13 低电平与灌电流上限引 DS5319 注 5；接线与命令以 `examples/gpio-blink`、`examples/uart-dma-idle` 的 README 为准（[附录 B](../appendix/B-project-index.md) 登记）。L0 三样证据与十八周排期见[第 46 章](../v7-delivery/46-resources-roadmap-open-source.md)，记录表格式见[第 40 章](../v6-labs-projects/40-lab-method-instruments.md)，失败分诊见[第 45 章](../v7-delivery/45-troubleshooting-handbook.md)。

## 一、这块芯片是什么

STM32 是意法半导体（ST）基于 ARM Cortex-M 内核的 32 位微控制器家族。一块最便宜的入门板（BluePill，STM32F103C8T6）上，有：一颗 72 MHz 的 Cortex-M3 内核、64 KB Flash、20 KB SRAM、一个能被 USB 主机识别的 USB 设备控制器、两路 CAN、三个 USART、以及几十个可以由你程序直接控制的引脚。

它能做什么？把它想成「一台可以焊进任何设备里的小电脑」：读传感器、驱动电机、点亮屏幕、连上网络、跟 PC 说话。全书的终点（[第 41 章](../v6-labs-projects/41-dual-board-logger-project.md)）是在两块板子上各做出一台完整的传感器记录器——采样、缓冲、上报、存配置、断线必停。起点则朴素得多：让一颗 LED 按你的节奏闪烁。

两个入门概念现在只需要记名字，机制各自有整章展开：

- **寄存器**：外设的「控制面板」，每个控制位对应一个内存地址。往那个地址写数，就是在按面板上的开关（[第 3 章](../v0-foundations/03-struct-abi-registers.md)、[第 9 章](../v1-drivers/09-gpio.md)）。
- **固件**：编译链接后烧进芯片 Flash 的程序。断电不丢，上电从复位向量第一行开始跑（[第 6 章](../v0-foundations/06-linker-startup-map.md)）。

## 二、买什么

两条装备线（完整清单与价格区间见[第 46 章](../v7-delivery/46-resources-roadmap-open-source.md)的采购表，价格是区间估算、以当日为准）：

| 装备 | 起步线（必买） | 用途 |
| --- | --- | --- |
| BluePill（STM32F103C8T6） | 一块 | 全书入门线的目标板；板载 PC13 LED |
| ST-Link V2 克隆 | 一个 | 烧录与调试（SWD 两线 + 电源） |
| USB-TTL 模块（3.3 V 档，CH340/CP2102） | 一个 | 串口对话（[第 13 章](../v1-drivers/13-uart-framed-protocol.md) 起） |
| 面包板 + 杜邦线 + 270 Ω 电阻 + LED | 若干 | 外接灯与后续外设实验 |

三条采购纪律：ST-Link 克隆先确认能被主机识别再扩展；USB-TTL 必须 3.3 V 电平档（5 V 直连 IO 会伤芯片）；共地永远先于信号（[第 45 章](../v7-delivery/45-troubleshooting-handbook.md) 的规则之二）。第二阶段再考虑 F407/ESP32-S3 的实战线装备，不提前囤。

## 三、装环境

本书例程的主路是 GNU Arm 嵌入式工具链 + Make（[第 5 章](../v0-foundations/05-toolchain-four-steps.md) 讲清了每一步在做什么，[第 7 章](../v0-foundations/07-build-systems-legacy.md) 给出工程组织）。装两样：

1. **GNU Arm Embedded Toolchain**（xPack 发行版或官方包）：提供 `arm-none-eabi-gcc` 与 binutils。
2. **Make**（Windows 装 xPack GNU Make 或 MSYS2 的）。

验证安装——这两条命令有输出，环境就绪：

```console
$ arm-none-eabi-gcc --version
arm-none-eabi-gcc (xPack GNU Arm Embedded GCC) 15.2.1
$ make --version
GNU Make 4.x
```

烧录工具用 ST-Link 自带的 STSW-LINK007 驱动加 OpenOCD 或 STM32CubeProgrammer（[第 20 章](../v2-reliability/20-debug-performance.md) 讲调试口的完整用法）。偏好图形环境的读者可以用 Keil MDK 或 STM32CubeIDE 走同样的例程——工程组织不同，四步机制相同（[第 7 章](../v0-foundations/07-build-systems-legacy.md)）。

## 四、第一次构建与烧录

例程：`examples/gpio-blink`（[附录 B](../appendix/B-project-index.md) 第 1 条）。它在一块 BluePill 上对比两组写法：HAL 库翻转与 `BSRR` 寄存器原子翻转，板载 LED（PC13）以 1 Hz 闪烁——亮 500 ms、灭 500 ms；外接 LED（PA0，经 270 Ω 限流电阻）每 5 秒翻转一次，用于确认程序没卡死。

构建与烧录：

```console
$ cd examples/gpio-blink
$ make
$ make flash
```

**你应该看到**（判读口径，转引例程 README 与 [第 7 章](../v0-foundations/07-build-systems-legacy.md)；本轮未实测，按预期现象记录）：

- `make` 结束无 error，产物里有 `build/*.elf`、`*.bin`；
- `make flash` 报告写入完成（OpenOCD/CubeProgrammer 的日志含 Flash write 字样）；
- 板载 PC13 LED 以约 1 Hz 闪烁——注意 PC13 是**低电平点亮**（共阳接法，灌电流能力见 DS5319 注 5 的 ≤3 mA、≤2 MHz 口径）；
- 接了外接灯的话，PA0 的 LED 每 5 秒翻转一次。

「灯不闪」的三条失败分支（完整分诊表见[第 45 章](../v7-delivery/45-troubleshooting-handbook.md) 与例程 README）：

| 症状 | 第一条假设 | 动作 |
| --- | --- | --- |
| 烧录工具找不到目标 | SWD 线序/驱动 | 查 ST-Link 枚举与四根线（SWDIO/SWCLK/3V3/GND） |
| 烧录成功但灯不闪 | 目标板没从 Flash 启动 | 查 BOOT0 跳线是否接 GND；复位一次 |
| 闪烁但外接灯反相 | 极性记反 | PC13 低电平点亮；PA0 高电平点亮 |

这一步做完，把三样证据记进[第 40 章](../v6-labs-projects/40-lab-method-instruments.md) 的记录表：构建日志（保存 `make` 输出）、烧录记录（工具与时间）、最小可见结果（一句话：PC13 约 1 Hz）。L0 的证据链就此闭合。

## 五、跟芯片说第一句话

点灯是「你 → 芯片」；串口是「芯片 → 你」。把 USB-TTL 模块接上：PA9（TX）接模块 RX，PA10（RX）接模块 TX（交叉），GND 共地，模块拨到 3.3 V 档。例程换 `examples/uart-dma-idle`，构建烧录同上。

打开串口终端（115200 8N1——这个数的来历与 BRR `0x271` 的算法在[第 13 章](../v1-drivers/13-uart-framed-protocol.md) 逐位拆过），发一条 `AT`：

**你应该看到**：终端返回 `OK`；`AT+LED=0` 点亮板载灯、`AT+LED=1` 熄灭、`AT+INFO` 返回固件信息串。三个坑提前给：不共地会乱码；5 V 电平直连会伤 IO；TX/RX 忘了交叉会「发了没回」。

到这里，你已经完成了上手卷的全部「看得见」部分——剩下的章节会告诉你：为什么时钟要那么配（[第 8 章](../v1-drivers/08-architecture-memory-clock.md)）、那个 `BSRR` 写入为什么是原子的（[第 9 章](../v1-drivers/09-gpio.md)）、`AT` 命令的每一字节是怎么进出的（[第 13 章](../v1-drivers/13-uart-framed-protocol.md)、[第 14 章](../v1-drivers/14-dma.md)）。

## 六、你现在的位置

L0 要求的证据你已经集齐：构建日志、烧录记录、复位后的最小可见结果。接下来两条路：

- **顺读**：进[第 1 章](../v0-foundations/01-c-memory-model.md)。它从「一个变量的两个地址」讲起——你刚才烧的固件里，每个全局变量都有这样两套地址；理解它，后面所有的段、链接与启动才有落点。
- **按周走**：[第 46 章](../v7-delivery/46-resources-roadmap-open-source.md) 的十八周排期把 46 章绑成一条每周都有可展示物的路线；本章是第 0 周（准备周），第 1 周从[第 7 章](../v0-foundations/07-build-systems-legacy.md)的构建系统开始。

无论哪条路，纪律只有一条：**每做完一步，留证据**。读数的来路比读数本身更重要（[第 40 章](../v6-labs-projects/40-lab-method-instruments.md)）。

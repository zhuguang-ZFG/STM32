---
title: "从开箱到点灯：买板、装环境与第一次下载"
platforms: [generic]
---

# 从开箱到点灯：买板、装环境与第一次下载

拿到新板子，先让 PC13 的 LED 亮 500 ms、灭 500 ms。本章带你完成第一次构建与烧录，留下构建日志、烧录记录和闪烁现象，作为 [L0 级别](../v7-delivery/46-resources-roadmap-open-source.md)的起步证据。

第一次点灯按这条路线走：

1. 核对板子、ST-Link 和接线，见「二、买什么」。已有装备就先核对，不必重复购买。
2. 选定一种开发环境，见「三、装环境」；第一次只用一种。
3. 按「四、第一次构建与烧录」建工程、下载、复位，观察 PC13 是否约 1 Hz 闪烁；失败时查该节的三条分支。
4. 保存三样证据，再继续「五、跟芯片说第一句话」。GPIO 和时钟的机制可以点灯后再读。

本章对应准备周（第 0 周）；后续十八周排期见[第 46 章](../v7-delivery/46-resources-roadmap-open-source.md)，第 1 周从构建系统开始。

![手绘板：第 0 周六站——从快递盒到 1 Hz（原理示意，非实拍）](/images/ch00-onramp-six-stops.png)

## 本章罗盘

- **问题**：新板子怎样完成第一次下载？灯不闪时，先查接线、启动方式还是程序？
- **交付**：完成一次从源码到闪烁的完整闭环，并留下 L0 要求的三样证据；遇到「灯不闪」时能按三条失败分支分诊；能用串口跟芯片完成第一次对话。
- **级别**：L0 起步。证据位置：「你应该看到」各清单与[第 40 章](../v6-labs-projects/40-lab-method-instruments.md) 的记录表；读完留下构建日志、烧录记录与一张填写过的记录表。
- **旅程导航**：从新板子走到构建、下载、点灯，再试串口。保存三样证据后进入 L0 后续学习。本章无板级实测，现象均为供你核对的预期。
- **开源读法**：本章的例程是 `examples/gpio-blink` 与 `examples/uart-dma-idle`（[附录 B](../appendix/B-project-index.md) 登记），README 里有完整接线与命令；工具链事实仍回[第 5 章](../v0-foundations/05-toolchain-four-steps.md)。
- **边界**：本章只做「跑起来」，不解释机制——GPIO 的寄存器语义在[第 9 章](../v1-drivers/09-gpio.md)，时钟树在[第 8 章](../v1-drivers/08-architecture-memory-clock.md)，串口在[第 13 章](../v1-drivers/13-uart-framed-protocol.md)；本章出现的数字（115200、BRR `0x271`、1 Hz）全部转引已冻结口径，不新造。
- **依据锚点**：点灯的 1 Hz、串口的 115200 与 BRR `0x271` 转引[第 7 章](../v0-foundations/07-build-systems-legacy.md)、[第 9 章](../v1-drivers/09-gpio.md)、[第 13 章](../v1-drivers/13-uart-framed-protocol.md)已冻结口径；PC13 低电平与灌电流上限引 DS5319 注 5；接线与命令以 `examples/gpio-blink`、`examples/uart-dma-idle` 的 README 为准（[附录 B](../appendix/B-project-index.md) 登记）。L0 三样证据与十八周排期见[第 46 章](../v7-delivery/46-resources-roadmap-open-source.md)，记录表格式见[第 40 章](../v6-labs-projects/40-lab-method-instruments.md)，失败分诊见[第 45 章](../v7-delivery/45-troubleshooting-handbook.md)。

## 一、这块芯片是什么

STM32 是意法半导体（ST）基于 ARM Cortex-M 内核的 32 位微控制器家族。一块常见的入门板（BluePill，[STM32F103C8T6](https://www.st.com/en/microcontrollers-microprocessors/stm32f103c8.html)）上，有：一颗 72 MHz 的 Cortex-M3 内核、64 KB Flash、20 KB SRAM、一个 USB 设备控制器、一路 CAN、三个 USART，以及几十个可以由你程序直接控制的引脚。

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

先在 Keil MDK、STM32CubeIDE、PlatformIO 中选一种，按例程 README 的「编译烧录」一节准备环境；已有其中一种就沿用。本章的 `examples/gpio-blink`、`examples/uart-dma-idle` 只带 `main.c`、接线图与 Wokwi 配置，没有附 Makefile 或 `CMakeLists.txt`，需要按所选环境新建工程，再加入例程。

本书后续的命令行构建主线是 GNU Arm 嵌入式工具链 + Make（[第 5 章](../v0-foundations/05-toolchain-four-steps.md)、[第 7 章](../v0-foundations/07-build-systems-legacy.md)）。走到那里时再准备以下工具，第一次点灯不必另装这一套：

1. **GNU Arm Embedded Toolchain**（xPack 发行版或官方包）：提供 `arm-none-eabi-gcc` 与 binutils。
2. **Make**（Windows 装 xPack GNU Make 或 MSYS2 的）。

验证安装——这两条命令有输出、版本号能打出来，PATH 就指对了：

```console
$ arm-none-eabi-gcc --version
arm-none-eabi-gcc (...) <你的版本号>
$ make --version
GNU Make <4.x 或更高>
```

版本号不必和本书一致：第 7 章的实测用的是 GNU Arm 10.3.1，换版本后四步产物与诊断信息会有出入，机制不变。

烧录先用所选环境的 ST-Link 下载功能；单独下载固件也可用 OpenOCD 或 STM32CubeProgrammer。Windows 下 ST-Link 的 USB 驱动是 [STSW-LINK009](https://www.st.com/en/development-tools/stsw-link009.html)；[STSW-LINK007](https://www.st.com/en/development-tools/stsw-link007.html) 用于升级 ST-Link 固件。完整调试口用法见[第 20 章](../v2-reliability/20-debug-performance.md)。

## 四、第一次构建与烧录

例程：`examples/gpio-blink`（[附录 B](../appendix/B-project-index.md) 第 1 条）。它在一块 BluePill 上对比两组写法：HAL 库翻转与 `BSRR` 寄存器原子翻转，板载 LED（PC13）以 1 Hz 闪烁——亮 500 ms、灭 500 ms；外接 LED（PA0，经 270 Ω 限流电阻）每 5 秒翻转一次，用于确认程序没卡死。

构建与烧录按例程 README 的「五、编译烧录步骤」三选一。本章不假设你用哪个 IDE，也不假设仓库里有一条统一的命令行：

1. **Keil MDK**：新建 F103C8 工程，把 `main.c` 覆盖到 `Core/Src/main.c`，编译后点下载。
2. **STM32CubeIDE**：新建 F103C8 工程，覆盖 `Core/Src/main.c`，编译后点运行/调试下载。
3. **PlatformIO**：工程里写 `board = bluepill_f103c8`、`framework = stm32cube`，把 `main.c` 放进 `src/`，再 `pio run -t upload`。

走 CubeMX/CubeIDE 这一路，记得在 `SYS → Debug` 选 **Serial Wire**（例程 README 的 CubeMX 配置表就是这么写的）：不选它，PA13/PA14 会被当成普通 GPIO，烧录一次之后就再也连不上板子。另外两路由各自的工程模板生成启动文件，SWD 是否被复用取决于模板；真遇到烧完连不上，回来查这一项。

**你应该看到**（判读口径，转引例程 README 与 [第 7 章](../v0-foundations/07-build-systems-legacy.md)；本轮未实测，按预期现象记录）：

- 编译无 error，工具在自己的输出目录里生成可执行固件（CubeIDE 在 `Debug/`、PlatformIO 在 `.pio/build/bluepill_f103c8/`、Keil 在 `Objects/` 且常见后缀是 `.axf` 而不是 `.elf`；文件名、后缀与是否附带 `.bin` 都以你的工具版本为准）；
- 下载/复位报告成功——以工具界面或终端打印为准（Keil、CubeIDE 显示下载完成，PlatformIO 打印 `SUCCESS`；改用 OpenOCD 烧录时，日志里要出现 Flash write 字样）；
- 板载 PC13 LED 以约 1 Hz 闪烁——注意 PC13 是**低电平点亮**（共阳接法，灌电流能力见 DS5319 注 5 的 ≤3 mA、≤2 MHz 口径）；
- 接了外接灯的话，PA0 的 LED 每 5 秒翻转一次。

<!-- stick-scene: ch00-unbox-blink -->

「灯不闪」的三条失败分支（完整分诊表见[第 45 章](../v7-delivery/45-troubleshooting-handbook.md) 与例程 README）：

| 症状 | 第一条假设 | 动作 |
| --- | --- | --- |
| 烧录工具找不到目标 | SWD 线序/驱动 | 查 ST-Link 枚举与四根线（SWDIO/SWCLK/3V3/GND） |
| 烧录成功但灯不闪 | 目标板没从 Flash 启动 | 查 BOOT0 跳线是否接 GND；复位一次 |
| 闪烁但外接灯反相 | 极性记反 | PC13 低电平点亮；PA0 高电平点亮 |

这一步做完，把三样证据记进[第 40 章](../v6-labs-projects/40-lab-method-instruments.md) 的记录表：构建日志（保存 IDE 的 Build 输出，PlatformIO 是 `pio run` 的日志）、烧录记录（工具与时间）、最小可见结果（一句话：PC13 约 1 Hz）。L0 的证据链就此闭合。

![手绘：ST-Link 的 SWDIO、SWCLK、GND 与 3.3 V 连接到 F103C8，电源或参考电压职能按下载器型号确认（原理示意，非实拍）](/images/ch00-swd-four-wires.png)

*先按接口丝印确认线序；这张图不表示不同下载器的 3V3 引脚都能给目标供电。*

## 五、跟芯片说第一句话

点灯是「你 → 芯片」；串口是「芯片 → 你」。把 USB-TTL 模块接上：PA9（TX）接模块 RX，PA10（RX）接模块 TX（交叉），GND 共地，模块拨到 3.3 V 档。例程换 `examples/uart-dma-idle`，建工程与烧录走同样的三选一（这个例程用 DMA + IDLE 收不定长，第一次跑只要命令能应答，机制留给[第 13 章](../v1-drivers/13-uart-framed-protocol.md)、[第 14 章](../v1-drivers/14-dma.md)）。

打开串口终端（115200 8N1——这个数的来历与 BRR `0x271` 的算法在[第 13 章](../v1-drivers/13-uart-framed-protocol.md) 逐位拆过），发一条 `AT`：

**你应该看到**：终端返回 `OK`；`AT+LED=0` 点亮板载灯、`AT+LED=1` 熄灭、`AT+INFO` 返回固件信息串。三个坑提前给：不共地会乱码；5 V 电平直连会伤 IO；TX/RX 忘了交叉会「发了没回」。

到这里，你已经完成了上手卷的全部「看得见」部分——剩下的章节会告诉你：为什么时钟要那么配（[第 8 章](../v1-drivers/08-architecture-memory-clock.md)）、那个 `BSRR` 写入为什么是原子的（[第 9 章](../v1-drivers/09-gpio.md)）、`AT` 命令的每一字节是怎么进出的（[第 13 章](../v1-drivers/13-uart-framed-protocol.md)、[第 14 章](../v1-drivers/14-dma.md)）。

![手绘：PA9 TX 接 USB-TTL RX、PA10 RX 接 USB-TTL TX，GND 共地，模块选 3.3 V 电平（原理示意，非实拍）](/images/ch00-uart-crossing.png)

*交叉处没有电气连接；AT → OK 是例程预期，本轮尚未上板验证。*

## 六、你现在的位置

L0 要求的证据你已经集齐：构建日志、烧录记录、复位后的最小可见结果。接下来两条路：

- **顺读**：进[第 1 章](../v0-foundations/01-c-memory-model.md)。它从「一个变量的两个地址」讲起：本书工程中，放在 `.data` 段的已初始化可写全局变量，初值存于 Flash，运行时在 RAM 中读写。沿着这次搬运，继续看段、链接与启动。
- **按周走**：[第 46 章](../v7-delivery/46-resources-roadmap-open-source.md) 的十八周排期把 46 章绑成一条每周都有可展示物的路线；本章是第 0 周（准备周），第 1 周从[第 7 章](../v0-foundations/07-build-systems-legacy.md)的构建系统开始。

无论哪条路，纪律只有一条：**每做完一步，留证据**。读数的来路比读数本身更重要（[第 40 章](../v6-labs-projects/40-lab-method-instruments.md)）。

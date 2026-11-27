---
title: "从开箱到点灯：买板、装环境与第一次下载"
platforms: [generic]
---

# 从开箱到点灯：买板、装环境与第一次下载

新板子到手，第一件事不是啃时钟树，而是让它闪起来：PC13 上的 LED 亮 500 ms、灭 500 ms。这条路线走完，你手里会多出构建日志、烧录记录和一段预期约 1 Hz 的闪烁——三样合起来，就是 [L0 级别](../v7-delivery/46-resources-roadmap-open-source.md)的起步证据。

第一次点灯按这条路线走：

1. 核对板子、ST-Link 和接线，见「二、买什么」。已有装备就先核对，不必重复购买。
2. 选定一种开发环境，见「三、装环境」；第一次只用一种。
3. 按「四、第一次构建与烧录」构建、下载、复位，观察 PC13 是否约 1 Hz 闪烁；失败时查该节的四条分支。
4. 保存三样证据，再继续「五、跟芯片说第一句话」。GPIO 和时钟的机制可以点灯后再读。

本章对应准备周（第 0 周）；后续十八周排期见[第 46 章](../v7-delivery/46-resources-roadmap-open-source.md)，第 1 周从构建系统开始。

![手绘板：第 0 周六站——从快递盒到 1 Hz（原理示意，非实拍）](/images/ch00-onramp-six-stops.png)

## 本章罗盘

- **问题**：新板子怎样完成第一次下载？灯不闪时，先查接线、启动方式还是程序？
- **交付**：完成一次从源码到闪烁的完整闭环，并留下 L0 要求的三样证据；遇到「灯不闪」时能按四条失败分支分诊；能用串口跟芯片完成第一次对话。
- **级别**：L0 起步。证据位置：「你应该看到」各清单与[第 40 章](../v6-labs-projects/40-lab-method-instruments.md) 的记录表；读完留下构建日志、烧录记录与一张填写过的记录表。
- **旅程导航**：从新板子走到构建、下载、点灯，再试串口。保存三样证据后进入 L0 后续学习。本章无板级实测，现象均为供你核对的预期。
- **开源读法**：`examples/gpio-blink` 与 `examples/uart-dma-idle` 都提供固定版本的完整 CMake 工程（[附录 B](../appendix/B-project-index.md) 登记）。先走通点灯，再复用依赖做串口；工具链事实见[第 5 章](../v0-foundations/05-toolchain-four-steps.md)。
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

第一次点灯使用 `examples/gpio-blink` 的完整工程。准备 Git、GNU Arm 工具链（含 newlib）、CMake ≥3.21 和 Ninja；下载另装 OpenOCD。先检查下面四条命令都有版本输出，找不到命令就先修 PATH：

```console
git --version
arm-none-eabi-gcc --version
cmake --version
ninja --version
```

本工程本机使用 GNU Arm 10.3.1 验证，CubeF1 固定为 `v1.8.6`，HAL 与 CMSIS 子模块提交自动核对。CMake 负责组织编译步骤，Ninja 执行；它们最终仍调用第 5 章的编译、汇编和链接工具。后续第 7 章另有 Make / SPL 对照，现在不用同时装齐。

已有 Keil 或 CubeIDE 环境可以沿用，但需按例程 README 另建对应工程，不能把它们当成本目录附带的项目。Windows 下 ST-Link 的 USB 驱动是 [STSW-LINK009](https://www.st.com/en/development-tools/stsw-link009.html)；[STSW-LINK007](https://www.st.com/en/development-tools/stsw-link007.html) 用于升级 ST-Link 固件。完整调试口用法见[第 20 章](../v2-reliability/20-debug-performance.md)。

![手绘：SysTick 中断推进 HAL 毫秒计数，主循环的两种等待读取同一时基；首个 tick 前为零是合法状态（原理示意，非实拍）](/images/ch00-hal-timebase.png)

## 四、第一次构建与烧录

例程：`examples/gpio-blink`（[附录 B](../appendix/B-project-index.md) 第 1 条）。板载 LED（PC13）目标约 1 Hz 闪烁，两段等待各约 500 ms；外接 LED（PA0，经 270 Ω 限流电阻）每 5 秒翻转一次。例程对比 HAL 翻转与读 ODR 后写 BSRR；单次 BSRR 写入原子，整个判断再翻转不是原子操作。

以下从仓库根目录执行。第一次需要网络下载固定依赖，之后按例程 README 复用已有检出：

```console
git clone --depth 1 --branch v1.8.6 https://github.com/STMicroelectronics/STM32CubeF1.git .temp/STM32CubeF1
git -C .temp/STM32CubeF1 submodule update --init Drivers/STM32F1xx_HAL_Driver Drivers/CMSIS/Device/ST/STM32F1xx
cd examples/gpio-blink
cmake --preset bluepill "-DCUBEF1_PATH=../../.temp/STM32CubeF1"
cmake --build --preset bluepill
```

构建成功后，在本例程目录下载：

```console
openocd -f interface/stlink.cfg -f target/stm32f1x.cfg -c "program build/bluepill/gpio-blink.elf verify reset exit"
```

先按下方 SWD 图核对供电、线序和 BOOT0=0，再运行下载命令。本工程保留 PA13/PA14 的 SWD 功能；若移植到 CubeMX，选 `SYS → Debug → Serial Wire`，并检查这两脚没有被外设占用。

**你应该看到**（判读口径，转引例程 README 与 [第 7 章](../v0-foundations/07-build-systems-legacy.md)；本轮未实测，按预期现象记录）：

- 编译无 error，在 `examples/gpio-blink/build/bluepill/` 生成 `gpio-blink.elf/.hex/.bin/.map`；
- OpenOCD 写入、verify 和复位成功，完整日志留存；
- 板载 PC13 LED 以约 1 Hz 闪烁——注意 PC13 是**低电平点亮**（共阳接法，灌电流能力见 DS5319 注 5 的 ≤3 mA、≤2 MHz 口径）；
- 接了外接灯的话，PA0 的 LED 每 5 秒翻转一次。

<!-- stick-scene: ch00-unbox-blink -->

灯不闪的时候，最容易被误导的是「程序没跑起来」这个判断。实际卡点通常落在四个地方，按顺序查（完整分诊表见[第 45 章](../v7-delivery/45-troubleshooting-handbook.md) 与例程 README）：

| 症状 | 第一条假设 | 动作 |
| --- | --- | --- |
| 烧录工具找不到目标 | SWD 线序/驱动 | 查 ST-Link 枚举与四根线（SWDIO/SWCLK/3V3/GND） |
| 烧录成功但灯不闪 | 目标板没从 Flash 启动 | 查 BOOT0 跳线是否接 GND；复位一次 |
| 翻转一次后停住 | SysTick 时基未推进 | 调试器多次继续/暂停读 uwTick；核对 SysTick_Handler 和中断屏蔽状态 |
| 闪烁但外接灯反相 | 极性记反 | PC13 低电平点亮；PA0 高电平点亮 |

这一步做完，把三样证据记进[第 40 章](../v6-labs-projects/40-lab-method-instruments.md) 的记录表：CMake/Ninja 构建日志、含 verify 的烧录记录（工具与时间）、最小可见结果（一句话：PC13 约 1 Hz）。只生成固件时，后两项仍填待测。

![手绘：ST-Link 的 SWDIO、SWCLK、GND 与 3.3 V 连接到 F103C8，电源或参考电压职能按下载器型号确认（原理示意，非实拍）](/images/ch00-swd-four-wires.png)

*先按接口丝印确认线序；这张图不表示不同下载器的 3V3 引脚都能给目标供电。*

## 五、跟芯片说第一句话

点灯是「你 → 芯片」；串口让芯片回话。把 USB-TTL 模块接上：PA9（TX）接模块 RX，PA10（RX）接模块 TX，GND 共地，模块选择 3.3 V 逻辑。先回到仓库根目录，再复用点灯时获取的 CubeF1：

```text
cd examples/uart-dma-idle
cmake --preset bluepill "-DCUBEF1_PATH=../../.temp/STM32CubeF1"
cmake --build --preset bluepill
python tests/check_firmware.py build/bluepill/uart-dma-idle.elf build/bluepill/uart-dma-idle.bin
openocd -f interface/stlink.cfg -f target/stm32f1x.cfg -c "program build/bluepill/uart-dma-idle.elf verify reset exit"
```

这是独立的串口工程，不会把 GPIO 固件改成串口。ARM 构建与宿主测试已通过，真实下载和收发仍待你在板上核对；DMA + IDLE 的机制留给[第 13 章](../v1-drivers/13-uart-framed-protocol.md)、[第 14 章](../v1-drivers/14-dma.md)。

打开串口终端（115200 8N1，无流控，关闭本地回显），发送 `AT` 并附加 `CRLF`。没有行尾时程序会继续等；只有输入框显示 `AT` 不能证明芯片回话。BRR `0x271` 的算法在[第 13 章](../v1-drivers/13-uart-framed-protocol.md)逐位拆过。

**你应该看到**：终端返回 `OK`；`AT+LED=0` 点亮板载灯、`AT+LED=1` 熄灭、`AT+INFO` 返回固件信息串。三个坑提前给：不共地会乱码；5 V 电平直连会伤 IO；TX/RX 忘了交叉会「发了没回」。

收到 `OK` 后再发 `AT+STATS`，保存原始响应。计数器帮助区分接收、软件丢失和 UART 错误，但普通 DMA 重装间隙仍可能丢字节，不能据一次握手推断连续流无损。

实际看到灯闪、收到板上 `OK` 并保存记录后，就能带着三个问题继续：时钟为什么这样配（[第 8 章](../v1-drivers/08-architecture-memory-clock.md)），`BSRR` 一次写入能保护什么（[第 9 章](../v1-drivers/09-gpio.md)），命令字节怎样拼回一行（[第 13 章](../v1-drivers/13-uart-framed-protocol.md)、[第 14 章](../v1-drivers/14-dma.md)）。

![手绘：PA9 TX 接 USB-TTL RX、PA10 RX 接 USB-TTL TX，GND 共地，模块选 3.3 V 电平（原理示意，非实拍）](/images/ch00-uart-crossing.png)

*交叉处没有电气连接；AT → OK 是例程预期，本轮尚未上板验证。*

## 六、你现在的位置

核对 L0 的三样证据：构建日志、烧录记录、复位后的最小可见结果。缺哪项就留在那一步补齐；全部完成后，接下来两条路：

- **顺读**：进[第 1 章](../v0-foundations/01-c-memory-model.md)。它从「一个变量的两个地址」讲起：本书工程中，放在 `.data` 段的已初始化可写全局变量，初值存于 Flash，运行时在 RAM 中读写。沿着这次搬运，继续看段、链接与启动。
- **按周走**：[第 46 章](../v7-delivery/46-resources-roadmap-open-source.md) 的十八周排期把 46 章绑成一条每周都有可展示物的路线；本章是第 0 周（准备周），第 1 周从[第 7 章](../v0-foundations/07-build-systems-legacy.md)的构建系统开始。

无论哪条路，纪律只有一条：**每做完一步，留证据**。读数的来路比读数本身更重要（[第 40 章](../v6-labs-projects/40-lab-method-instruments.md)）。

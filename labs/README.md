# 证据实验

这里放「怎样才算在真板上做完」的协议，不放可编译示例。代码入口见各协议；根目录 HAL 示例与 `mcu/code/` 的寄存器工程不混用。

| 实验 | 现行章节 | 工程 / 主机工具 | 当前边界 |
| --- | --- | --- | --- |
| [点灯](gpio-blink/README.md) | [ch00](../docs/onramp/00-from-box-to-blink.md)、[ch09（E01 方法）](../docs/v1-drivers/09-gpio.md) | `mcu/code/stm32/00-blink` | 协议与源码静态核对；未实测 |
| [PWM](timer-pwm/README.md) | [ch12（E03 方法）](../docs/v1-drivers/12-timers-pwm.md) | `mcu/code/stm32/02-tim-pwm` | 协议与源码静态核对；未实测 |
| [UART](uart-dma/README.md) | [ch13（E02 方法）](../docs/v1-drivers/13-uart-framed-protocol.md)、[ch14](../docs/v1-drivers/14-dma.md) | `mcu/code/stm32/03-uart-dma` | 协议与源码静态核对；未实测 |
| [ethernet-24h](ethernet-24h/) | [ch33](../docs/v4-platforms/33-network-protocol-stack.md) | [tools/ethernet_soak.py](../tools/ethernet_soak.py) | 沿原协议，本轮未执行 |

学习依赖与阶段验收沿用 [ch46](../docs/v7-delivery/46-resources-roadmap-open-source.md)，仪器纪律沿用 [ch40](../docs/v6-labs-projects/40-lab-method-instruments.md)。三个协议复用 E01/E03/E02 的方法，不另编实验编号。

## 验证状态

2026-11-18 文档审阅未连接板卡/调试器，未构建或下载固件，未新增硬件读数；三个协议均为 `hardware_status: pending`。文档完整不等于已可硬件复现，工具或驱动存在也不证明连接了某块板。

## 开始前：身份与供电安全（未满足即停止）

1. 拍实际板卡型号/版本、芯片丝印、供电跳线与调试器型号。三个主工程的启动文件声明 STM32F407ZGT6，源码 LED 对应霸天虎口径，链接脚本为 Flash 1MB / SRAM 128KB。实际板卡、芯片与容量均**待核实**；其他封装或板型不能直接套用。
2. 断电核对实际原理图、SWD 针序和电源：SWDIO/PA13、SWCLK/PA14、GND、目标电压参考。VTref 不能默认当供电输出。使用单一合规板电源，不未经核对同时接 USB、调试器与 USB-TTL 供电；先地后信号，不带电换线。
3. 仅用 3.3V 逻辑；不把5V或 RS-232 正负电压接 GPIO。USB-TTL 的 VCC 不接作板电源，只接 TX/RX/GND。外接 LED 须有限流，不用 GPIO 直接带功率负载。
4. 示波器地夹只接板 GND，不夹正电源或浮动功率节点；逻辑分析仪先核耐压、共地。万用表不要在电流孔量电压；排除短路和超额供电后才上电。

## 构建与烧录边界（供后续执行，本轮未执行）

三份 F407 工程均有 Makefile/main.c/启动文件/链接脚本；PWM/UART 还引用 `mcu/code/common/behavior/`，须保留仓库相对结构。现有 Makefile 使用 Cortex-M4、hard float、默认 `-O0 -g3`，不需要另下载 HAL。

- 环境需要 `arm-none-eabi-gcc`、`arm-none-eabi-objcopy`、`arm-none-eabi-size`、GNU Make；Windows 原说明使用 mingw32-make 和 Git 的 `usr/bin`，Makefile 有 `mkdir -p` 等 shell 配方，须记录实际 Make 命令名与兼容 shell。工具缺失时登记缺口，不在本轮下载。
- 各协议的 `make`/`make flash` 均来自现有 Makefile。先构建成功，保存完整日志、版本、源码提交 SHA 与未提交差异，再记录 ELF/BIN 的 SHA-256。构建失败停止，不用旧固件替代。
- `make flash` 使用 OpenOCD 的 `interface/stlink.cfg` 和 `target/stm32f4x.cfg`，执行 `program ...elf verify reset exit`。身份、安全和后续写板授权均确认后才运行；保存 verify/退出码，冷复位复核现象。
- 既有 `make debug`/`make gdb` 分两终端；**gdb 目标含 load，也会写板**，不是只读观察。不要为本轮文档核对运行它们。
- F103 对照 `examples/gpio-blink`、`examples/timer-pwm` 只有 HAL main.c 与 Wokwi 配置，没有独立完整构建工程；须由实际工程提供 HAL/CMSIS、启动、链接和 SysTick 中断时基。本轮不生成骨架、不承诺一条命令能构建。

## 共用证据记录（复制到仓库外，所有实测栏待测）

复用上一轮 `hardware-next.md` 的取证计划与 ch40「押注→测量→对账→登记」：理论计算、寄存器推导、仪器实测、未验证分别标明，不能把 g_* 公式推导值称为仪器测量。

| 字段 | 本次记录 |
| --- | --- |
| 日期时间（Asia/Shanghai）、执行人 | 待填（未实测） |
| 板型/版本、芯片丝印/ID/容量、供电与调试器 | 待核实（未连接） |
| 代码路径、提交 SHA、工作区差异、工具链路径/版本、构建命令 | 待执行/登记 |
| ELF/BIN SHA-256、构建日志、烧录/verify/冷复位日志 | 待生成（未构建/未烧录） |
| 接线照片、仪器型号/校准、探头倍率、采样率/时基/触发 | 待记录 |
| 寄存器回读与理论公式/输入/单位/适用条件 | 计算与读数分栏；回读待测 |
| 测量前确定的允许误差及来源 | 待定；来自时钟规格、仪器与量化误差；未知不判精度通过 |
| 原始读数、波形/逻辑采样/字节日志及计算过程 | 待测（不得填入理论数） |
| 偏差、失败分支、复测条件与复测结果 | 待测 |
| 结论与未证明事项 | 未实测，不能宣布硬件可复现/实测通过 |

原始照片、波形、日志、JSONL 和抓包放仓库外证据目录，文档登记索引与哈希，不提交临时日志。缺前提标「阻塞」，缺实测标「待测」，不能填「通过」。独立练习是后续任务，不代表本轮改变固件行为。

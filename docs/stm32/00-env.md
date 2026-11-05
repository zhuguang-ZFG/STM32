---
title: S0 环境搭建：裸机工具链
status: done
difficulty: 1
minutes: 25
---

# S0 环境搭建：裸机工具链，四个软件看透全流程

![环境搭建五步闭环](/anim/env-setup-flow.svg)

> 🎯 你买了一台顶配的"全自动咖啡机"（IDE），按一下就出咖啡，但豆子什么时候磨的、水温几度，你一概不知。这一章我们反着来：手动磨豆、手动控温。等你会了，再回去用咖啡机也不迟。

动手之前先押个分工：从一行 C 源码到板上灯亮，这一路要过工具链四件套的手。真正把 C 翻译成 ARM 机器码的是谁？把编译产物送进芯片的又是谁？押完再往下装，记忆锚点那节对答案。

## 本章精髓

1. 为什么坚持不用 CubeIDE/Keil 起步？因为 IDE 把"预处理→编译→汇编→链接→烧录"藏进一个按钮，而这条链路本身就是嵌入式的半壁江山（[B 篇](../build/index.md)整个都在讲它）。
2. 交叉编译到底"交叉"在哪？在 x86 电脑上，产出 ARM Cortex-M4 的机器码。
3. 一个能跑的固件最少需要几个文件？四个：启动文件、链接脚本、main、Makefile。我们已经备好：[code/stm32/00-blink](https://github.com/zhuguang-ZFG/mcu/tree/main/code/stm32/00-blink)。

## 先修

- 无。这是起点。唯一要求：Windows 10/11 + 一块霸天虎 + 一个 ST-Link（或兼容的 J-Link/DAP）。

## 装备清单

| 装备 | 用途 | 备注 |
|---|---|---|
| [野火 F407 霸天虎](https://doc.embedfire.com/products/link/zh/latest/mcu/stm32/stm32f407_batianhu.html) | 目标板 | 板载 RGB 灯 PF6/7/8；板卡外观与原理图见官方资料页 |
| ST-Link V2（或 J-Link/DAP） | 烧录+调试 | 霸天虎**不板载**仿真器，必须自备 |
| Micro-USB 线 ×2 | 板子供电、仿真器连接 | 别拿成充电专用线（没数据线芯） |
| 杜邦线若干 | 接 SWD | 若仿真器带排线可省 |

![基于 STM32F407 的第三方开发板](/images/boards/stm32f407-board.jpg)

> F407 家族板卡形态参考：图为一款第三方 F407VET6 板（LQFP100）；本站基准板霸天虎为 F407ZGT6/LQFP144，外观不同、芯片同门（来源：[Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Embedded_World_2016,_STM32_F407_VGT6.jpg)，CC0）。

## 第一步：装 ARM 交叉编译器

1. 打开 Arm 官网开发者页，搜 **"Arm GNU Toolchain"**，下载 Windows 版 `arm-gnu-toolchain-14.x.rel*-mingw-w64-x86_64-arm-none-eabi.exe`。
2. 安装，**最后一步务必勾选 "Add path to environment variable"**。
3. 开一个**新的**终端验证（PATH 改了必须重开终端）：

```bash
arm-none-eabi-gcc --version
```

看到 `gcc version 14.x.x` 即成功。`arm-none-eabi` 读作"ARM、无厂商、嵌入式应用二进制接口"（专门为裸机 ARM 产代码的 GCC）。

## 第二步：装 make

Windows 没有自带 make。最省心的来源是 **xPack Windows Build Tools**：

1. 搜 "xPack Windows Build Tools"，下载最新 `xpack-windows-build-tools-*-win32-x64.zip`。
2. 解压到无中文无空格路径（如 `D:\tools\xpack-build-tools`）。
3. 把其 `bin` 目录加入系统 PATH，新开终端验证：

```bash
make --version
```

## 第三步：装 OpenOCD（烧录与调试的桥梁）

1. 搜 "xPack OpenOCD"，下载 Windows 版 zip 并解压（同样避开中文/空格路径）。
2. `bin` 目录加入 PATH，验证：

```bash
openocd --version
```

OpenOCD 的角色：一边通过 USB 跟 ST-Link 说话，一边通过 SWD 协议跟芯片说话，把我们的 `program` 命令翻译成对 Flash 的擦写。SWD 只有两根信号线（SWDIO 数据 + SWCLK 时钟），[B6 章](../build/06-flash-debug.md)会把它讲透。

## 第四步：ST-Link 驱动

- **正版 ST-Link / ST-Link V2**：装 ST 官方的 **STSW-LINK009** USB 驱动（搜 ST 官网编号）。
- **DAPLink（CMSIS-DAP）**：Windows 10/11 免驱，插上即用。
- 验证：插上仿真器，设备管理器里应出现 "STM32 STLink" 或对应设备，**没有黄色感叹号**。

## 第五步：接线（SWD 四线）

| ST-Link | 霸天虎 SWD 座 |
|---|---|
| SWDIO | SWDIO |
| SWCLK | SWCLK |
| GND | GND |
| 3.3V | 3.3V（仅作检测，不给板子供电；板子单独 USB 供电） |

::: warning 供电纪律
板子用自己的 USB 供电，仿真器的 3.3V 只接检测脚。两路电源对供是烧板的经典姿势。
:::

## 第六步：构建第一个工程

进入仓库的工程目录，一条命令：

```bash
cd code/stm32/00-blink
make
```

预期输出：

```text
arm-none-eabi-gcc ... -c main.c -o build/main.o
arm-none-eabi-gcc ... -o build/blink.elf
   text    data     bss     dec
   ~200       0       0    ~200   build/blink.elf
```

产物全家福：

| 产物 | 是什么 |
|---|---|
| `blink.elf` | 带调试信息的完整固件（GDB 用它） |
| `blink.bin` | 纯二进制镜像（可直接按地址烧） |
| `blink.hex` | Intel HEX 文本格式（烧录器通用） |
| `blink.map` | 每个符号的地址清单——[B5 章](../build/05-map-size.md)教你审计它 |

构建失败？先去对照[常见坑](#常见坑)，90% 的问题在那里。

## 第七步：烧录，点灯！

```bash
make flash
```

OpenOCD 刷出一串日志，关键看三行：

```text
** Programming Started **
** Verified OK **
** Resetting Target **
```

然后——**霸天虎上的红灯开始以约 1Hz 呼吸闪烁**。这不是 IDE 里按出来的，是你亲手从四个文本文件变出来的。

## 第八步（选做）：GDB 看一眼寄存器

```bash
make debug     # 终端 1：OpenOCD 常驻
make gdb       # 终端 2：连上后自动复位、烧录、断在 main
```

在 GDB 里：

```gdb
continue          # 跑过 GPIO 配置
x/wx 0x40023830   # RCC_AHB1ENR：bit5 应该是 1（GPIOF 时钟开了）
```

`0x40023830` 这个地址不是魔法：RCC 基址 0x40023800 + 寄存器偏移 0x30，查 RM0090 §7.3 一字不差。[C2 指针章](../c/02-pointer.md)会讲清"往地址写字"的全部原理。

## 记忆锚点

::: tip 一句话记住
**工具链四件套：gcc 翻译、make 指挥、OpenOCD 送信、ST-Link 跑腿。** 固件四文件：启动文件开门、链接脚本排座、main 干活、Makefile 记账。
:::

**延伸**：环境搭建五步闭环动画见 [S0 动画](/anim/env-setup-flow.svg)；工具链四件套详解在 [B0](../build/00-toolchain.md)；四步构建流程在 [B1](../build/01-four-steps.md) 展开。

## 实物实验

本章就是实验本身。观测点与预期：

- `make` 后 `build/` 下出现 elf/bin/hex/map 四个文件；
- `make flash` 日志出现 `Verified OK`；
- 复位后 PF6 红灯约 1Hz 闪烁（HSI 16MHz 软件延时，频率不准属正常，[S5 SysTick](05-systick.md) 再较真）。

## 短自测

1. "交叉编译"的"交叉"具体指什么？为什么不能直接用电脑上的 gcc？
<details><summary>参考答案</summary>交叉指"编译环境"与"运行环境"的 CPU 架构不同：你在 x86-64 的 Windows 上编译，产出的是 ARM Cortex-M4 的机器码。电脑上的 gcc 默认产出 x86 指令，Cortex-M 无法执行；`arm-none-eabi-gcc` 才是 ARM 目标的后端。`none` 表示没有操作系统（裸机），`eabi` 是 ARM 嵌入式 ABI。</details>

2. `make` 之后 `build/` 下出现 elf、bin、hex、map 四个文件。分别是什么用途？烧录用哪个？
<details><summary>参考答案</summary>**elf**：完整的 ELF 固件，含代码、数据、调试信息和符号表：调试用它的符号，烧录用它的二进制内容。**bin**：纯二进制镜像，从地址 0x08000000 起的逐字节拷贝，烧录最快。**hex**：Intel HEX 格式，每行带地址和校验，可描述不连续的内存区域。**map**：链接器输出的符号地址清单，不含机器码，用于查"函数住在第几字节"。烧录用 bin 或 hex 均可（OpenOCD 两种都接受），调试必须用 elf。</details>

3. Makefile 里命令行首为什么必须是 Tab 而不是空格？报 `missing separator` 怎么修？
<details><summary>参考答案</summary>Make 的语法规则：规则体（recipe）的每一行必须以 **Tab 字符**开头，空格不被识别为命令行。这是 1970 年代 Make 的原始设计，至今未改。某些编辑器（VS Code 默认不犯，但 Notepad++ 和某些 IDE 的"智能缩进"模式会）会把 Tab 自动替换成空格。修复方法：在编辑器里关闭"用空格替换 Tab"，或直接用 `sed -i 's/^    /\t/' Makefile` 把行首四空格换成 Tab。</details>

## 常见坑

- **`'arm-none-eabi-gcc' 不是内部或外部命令`**：PATH 没生效。装了新工具必须**重开终端**；还不行就是安装时没勾 Add path，手动加。
- **make 报 `missing separator`**：Makefile 的命令行首必须是 **Tab 不是空格**。某些编辑器会把 Tab 转成空格。
- **OpenOCD 报 `Error: open failed` / 找不到 ST-Link**：九成是驱动（回第四步）；一成是杜邦线虚接：SWD 对接触很敏感，重新插拔。
- **灯不亮但烧录成功**：先怀疑引脚号。霸天虎是 **PF6**；网上大量教程是其他板子的 PA8/PF9，照搬必翻车。
- **解压路径有中文/空格**：xPack 系工具对非 ASCII 路径敏感，装 `D:\tools\` 这种纯英文路径。
- **两台 USB 设备抢供电**：仿真器 3.3V 和板子 USB 供电不要同时怼，见第五步警告。

## 你做到了

- 电脑变成了交叉编译工作站，四件工具各司其职。
- 亲手构建了固件四产物，知道每个是干什么的。
- 红灯在你自己的代码控制下闪烁，裸机世界的 Hello World 达成。

<div class="achievement">
✅ 下一站：<a href="01-arch.html">S1 F407 架构总览</a>：0x40020000 凭什么就是 GPIOA？总线矩阵和存储器映射把门牌号拆开给你看。状态：本章代码已静态核对 RM0090，<strong>待上板实测反馈</strong>（欢迎 Issue 报告你的现象）。
</div>

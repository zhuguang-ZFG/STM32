---
title: G0 环境与工具链：复用一套 GCC，解剖官方库 V3.3.3
status: done
difficulty: 2
minutes: 25
---

# G0 环境与工具链：复用一套 GCC，解剖官方库 V3.3.3

> 🎯 STM32F407 你装过 xPack arm-none-eabi-gcc——好消息：GD32F4xx 也是 Cortex-M4F，同一套交叉编译器一个字都不用改就能编。要换的只有"事实字典"：把 ST 的 CMSIS 头文件换成兆易创新的官方固件库 V3.3.3。本章就把这本字典的目录拆给你看。

![通用环境搭建五步闭环：安装→配置→编译→烧录→点灯](/anim/env-setup-flow.svg)

## 本章精髓

1. **工具链零增量**：GD32F4xx 是 ARM Cortex-M4F，交叉编译旗 `-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard` 与 STM32F407 **逐字相同**（B0 已装好的 xPack arm-none-eabi-gcc 15.2.1 直接复用）；只需多一个 `-DGD32F450` 选芯片型号。
2. **官方库 V3.3.3 是两层结构**：上层是 **CMSIS 设备层**（`gd32f4xx.h` + `system_gd32f4xx.c` + 启动模板），下层是 **标准外设库层**（`gd32f4xx_rcu.h/.c`、`gd32f4xx_gpio.h/.c`……每个外设一对）。所有头文件统一标 `version 2026-02-05, V3.3.3`。
3. **本站 GD32 工程是"寄存器级"，不 `-I` 官方库**：官方 `.h` 当**事实字典**读（查偏移、查位名），main.c 里手写 `*(volatile uint32_t*)` 访问，和 S 篇同款姿势。官方库源码缓存于 `.trellis/ref/gd32/`，不随仓库分发。

- **能理解**：为什么 GD32 不需要装新编译器（同为 Cortex-M4F，ABI 一致）；官方库 `.h` 与 `.c` 各自的角色。
- **能用**：拿到一份 GD32F4xx 工程，能指出哪个文件来自 CMSIS 设备层、哪个来自标准外设库层，并自己加一个外设的头文件进来。

## 先修

- 无强制先修；建议先读 [B0 工具链全景](../build/00-toolchain.md) 把 xPack arm-none-eabi-gcc 装好，再看 [S0 环境](../stm32/00-env.md) 的安装步骤对照。

## 先跑起来（10 分钟 quick win）

确认你电脑上那套 xPack 工具链能编 GD32。在仓库根目录跑：

```bash
arm-none-eabi-gcc --version    # 应显示 15.2.1（xPack，与 CI 同源）
cd code/gd32/01-rcu-clock && make    # G1 工程，编过就说明工具链对 GD32 也通
```

先押个开箱单：行李是零，三件套还是三张老面孔。谁管向量表、谁把时钟树拉到 200MHz、谁划 Flash 和 SRAM 的地盘？押完再敲 make。

`make` 走完应该看到 `arm-none-eabi-size` 打印 text/data/bss 三列体积，和 S 篇工程长得一模一样。这一条证明：**编 STM32 和编 GD32，是同一套 gcc、同一组编译旗，只是源码和链接脚本换了**。

## 小节结构

| 小节 | 内容 |
|---|---|
| 一、工具链复用 | 同一颗 Cortex-M4F，编译旗逐字相同；`-DGD32F450` 选型号 |
| 二、官方库两层结构 | CMSIS 设备层 + 标准外设库层；目录解剖 |
| 三、三件套：启动 / system / 链接脚本 | startup_gd32f4xx.s、system_gd32f4xx.c、gd32f4xx.ld |
| 四、寄存器级工程怎么"用"官方库 | .h 当字典读，main.c 手写访问 |

## 一、工具链复用：同一套 GCC 编两颗芯

GD32F4xx（F450/F470）的内核是 **ARM Cortex-M4F**，和 STM32F407 同一个内核、同一套 FPU（FPv4-SP-D16）、同一套 AAPCS 硬浮点 ABI。所以 [B0](../build/00-toolchain.md) 装好的 xPack arm-none-eabi-gcc 15.2.1，编 GD32 不用动一个字节。

实证看 G1 工程的 Makefile（`code/gd32/01-rcu-clock/Makefile:8-11`）：

```make
CC      := arm-none-eabi-gcc
CFLAGS  := -mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard \
           -g3 -O1 -Wall -Wextra -std=c11 -ffreestanding -fno-builtin \
           -DGD32F450 \
           -Wa,--noexecstack
```

把这套旗和 S 篇工程并排看：`-mcpu/-mthumb/-mfpu/-mfloat-abi` 四件**完全相同**（这四件描述的是"ARM Cortex-M4F 这个内核"，与芯片厂无关）。唯一的 GD32 专属是 `-DGD32F450`：它是一个**型号选择宏**，官方 `gd32f4xx.h` 顶部根据它挑出 Flash/RAM 容量、中断向量条数等型号相关参数。

> **【注】为什么 GD32 不需要"GD32 专用编译器"？** 交叉编译器的 target 是 **ARM 体系**（`arm-none-eabi-` 的 `arm`），不是某家芯片厂。Cortex-M4F 是 ARM 设计的内核，STM32F407 和 GD32F450 都买这同一个内核，所以同一套 gcc 都能编。芯片厂的差异在外设（RCU/GPIO/USART 寄存器布局），那部分由 **CMSIS 设备头文件** 描述，不归编译器管。这是"学透一颗再举一反三"能成立的底层原因。

工具链自查纪律照搬 B0：`arm-none-eabi-gcc --version` 看版本、`-print-search-dirs` 看搜索路径、`where arm-none-eabi-gcc`（Windows）看 PATH 优先级。本站 CI 的 arm-host job 与本地同源 xPack 15.2.1，本地能编过 CI 就能编过。这条对 STM32 和 GD32 一视同仁。

## 二、官方库 V3.3.3 两层结构：目录解剖

兆易创新放出的 **GD32F4xx Firmware Library V3.3.3** 是一个标准固件包，分两层。本站参考缓存 `.trellis/ref/gd32/` 收录的是这两层的关键文件子集（按版本核对，`@10d02f4`）：

```
GD32F4xx_Firmware_Library_V3.3.3/
├── Firmware/
│   ├── CMSIS/
│   │   └── GD/GD32F4xx/
│   │       ├── Include/                    ── 设备头：gd32f4xx.h、system_gd32f4xx.h
│   │       └── Source/
│   │           ├── system_gd32f4xx.c       ── 时钟树/系统初始化（G1 全章解剖）
│   │           └── Templates/             ── 启动文件：gcc/startup_gd32f4xx.s 等
│   └── GD32F4xx_standard_peripheral/
│       ├── Include/                        ── gd32f4xx_rcu.h、gd32f4xx_gpio.h、gd32f4xx_usart.h …
│       └── Source/                         ── gd32f4xx_rcu.c、gd32f4xx_gpio.c …
└── Examples/                               ── 外设示例（G1 提到全量约 3295 个文件）
```

两层分工：

| 层 | 代表文件 | 角色 | 本站用法 |
|---|---|---|---|
| **CMSIS 设备层** | `gd32f4xx.h`、`system_gd32f4xx.c` | 描述"这颗芯片"：基址、中断号、寄存器总线挂载；`system_*.c` 是上电后第一段 C 代码（时钟树初始化） | `gd32f4xx.h` 是**事实总字典**（G1 的 RCU 基址、G2 的 GPIO 基址全从这里查） |
| **标准外设库层** | `gd32f4xx_rcu.h/.c`、`gd32f4xx_gpio.h/.c` | 每个外设一对：`.h` 给寄存器位定义 + 库函数原型，`.c` 给库函数实现 | `.h` 当位域字典读；`.c` 看官方"标准做法"对照（G1 第七节就是逐行对照 `system_gd32f4xx.c`） |

版本取证：每个 `.h` 顶部都印一行 `version 2026-02-05, V3.3.3, firmware for GD32F4xx`（见 `gd32f4xx_gpio.h:5`），这是本站"按版本核对"的锚点。

> **【注】目录路径以官方包 README 为准。** 上面这棵树是 GD32 固件库 V3.3.3 的**标准包布局**：文件夹名（`Firmware/CMSIS/GD/GD32F4xx/...`）遵循兆易创新一贯的打包约定。本站仓库不随包分发，只在 `.trellis/ref/gd32/` 缓存了关键 `.h/.c` 用于事实核对；要完整跑官方 Examples，需自行从兆易创新官网下载 V3.3.3 包。具体顶层文件夹名如有更新，以官方包 README 为准（**待官方包核对**）。

## 三、三件套：启动文件、system 文件、链接脚本

把一颗 GD32F4xx 从复位跑到 `main()`，最少要三个文件，本站 G1 工程三个都齐了：

| 文件 | 来源 | 干什么 |
|---|---|---|
| `startup_gd32f4xx.s` | 官方 `Templates/` 的 GCC 版（本站按教学精简） | 向量表（16 内核槽 + 82 外设槽）+ Reset_Handler：开 FPU → 拷 `.data` → 清 `.bss` → `main` |
| `system_gd32f4xx.c` | 官方 CMSIS 设备层 | `SystemInit()`：上电后第一段 C，配时钟树到 200MHz（G1 全章解剖） |
| `gd32f4xx.ld` | 自写（参考官方 GCC 链接脚本） | 内存映射：Flash 起始 0x08000000、SRAM 起始 0x20000000、堆栈位置 |

- **启动文件**：官方 `Templates/` 同时给 **ARM（Keil）/IAR/GCC** 三套启动文件，因为这三家工具链的汇编语法、段名约定不同。本站用 GCC 版（`.s` 用 GNU 汇编语法，`.syntax unified`、`.thumb_func`）。G1 的 `startup_gd32f4xx.s` 在官方基础上**精简为弱符号 + Default_IRQHandler**（向量槽统一填弱符号，应用可同名覆盖，见 `code/gd32/01-rcu-clock/startup_gd32f4xx.s:30-33`）。
- **system 文件**：这是 GD32 与 STM32 的一个关键差异点：`system_gd32f4xx.c` 里 `SystemInit()` 把 PLL 直接拉到 **200MHz**（F450 档），而 ST 的 `system_stm32f4xx.c` 默认留在 168MHz。G1 整章就是解剖这个文件，这里只点名它的存在。
- **链接脚本**：`gd32f4xx.ld` 描述 GD32F4xx 的 Flash/RAM 地址范围。Flash 基址 `0x08000000`、SRAM 基址 `0x20000000`，这俩是 ARM Cortex-M 的约定，和 STM32F4 相同；具体容量（F450/F470 不同）由 `-DGD32F450` 选定的型号决定。链接脚本的写法和 [B3 链接脚本](../build/03-linker-script.md) 同款，只是地址表换成了 GD32 的。

## 四、寄存器级工程怎么"用"官方库

本站 GD32 工程和 S 篇一样是**寄存器级**：不调官方库函数、不 `-I` 官方库头文件，main.c 自己手写 `*(volatile uint32_t*)` 访问寄存器。那官方库拿来干嘛？**当事实字典读**。

以 G1 工程为例（`code/gd32/01-rcu-clock/main.c:23-29`）：

```c
/* ================= 基地址（gd32f4xx.h @10d02f4） ================= */
#define AHB1_BUS_BASE   0x40020000U
#define RCU_BASE        (AHB1_BUS_BASE + 0x3800U)   /*!< RCU（gd32f4xx.h:343） */
#define FMC_BASE        (AHB1_BUS_BASE + 0x3C00U)   /*!< FMC（gd32f4xx.h:344） */
#define PMU_BASE        (APB1_BUS_BASE + 0x7000U)   /*!< PMU（gd32f4xx.h:330） */
```

每个 `#define` 后面都挂了**凭证行号**：`gd32f4xx.h:343` 是 RCU 基址的出处。写代码的人打开 `.trellis/ref/gd32/gd32f4xx.h`，跳到第 343 行，抄下 `RCU_BASE = AHB1_BUS_BASE + 0x3800`，再回到 main.c 写宏。**官方 `.h` 是字典，main.c 是作文**——字典不进作文，但作文每个字都得查过字典。

这套"读字典、手写访问"的姿势带来三个好处：

1. **事实可核验**：每个魔法数字都挂了头文件行号，读者一条条能对得上（G1 的"事实来源"表就是这么来的）。
2. **不绑死官方库版本**：V3.3.3 升到 V3.4，库函数签名可能变，但寄存器偏移不会变，寄存器级代码跨版本稳。
3. **对照 STM32 一目了然**：手写 `RCU_AHB1EN` 和手写 `RCC_AHB1ENR` 并排看，"同名不同姓"立刻显形（这正是 G1/G2 的写法）。

> **【注】什么时候才真的链接官方库 `.c`？** 当你想要库函数的便利（`gpio_af_set()` 一行配好 AF）、又不在乎版本绑定时，把 `gd32f4xx_gpio.c` 加进 `SRCS`、把 `Include/` 加进 `-I` 即可。本站教学工程为了"寄存器级透明"选择不链接，但 G2 会把官方 `gpio_mode_set` / `gpio_af_set` 的实现拆给你看，证明它就是我们手写那几行的 for 循环封装。

## 记忆锚点

::: tip 一句话记住
**工具链零增量（同 Cortex-M4F）、官方库两层（CMSIS 设备层 + 标准外设库层）、三件套（启动/system/链接脚本）；本站工程读 `.h` 当字典、手写访问，魔法数字挂行号。**
:::

**延伸**：环境搭建五步闭环动画见 [G0 动画](/anim/env-setup-flow.svg)；STM32 工具链对照见 [B0](../build/00-toolchain.md)；SPL 库结构解剖见 [S15](../stm32/15-spl-anatomy.md)。

## 实物实验

- **quick win 复现**：`cd code/gd32/01-rcu-clock && make`，看到 `size` 打印三列体积，证明 xPack 工具链对 GD32 通。
- **目录自检**：打开 `.trellis/ref/gd32/`，数一数 CMSIS 设备层文件（`gd32f4xx.h`、`system_gd32f4xx.c`）与标准外设库文件（`gd32f4xx_rcu.h`、`gd32f4xx_gpio.h`、`gd32f4xx_fmc.h`……）各几个，印证两层结构。
- **型号对照（选做）**：把 Makefile 的 `-DGD32F450` 暂改成 `-DGD32F470`，看 `gd32f4xx.h` 顶部 `#ifdef` 分支怎么挑容量。型号选择宏已实证：`gd32f4xx.h:46` 列出 6 种型号（F450/F405/F407/F470/F425/F427），F450 与 F470 共享容量分支（:171-213）；F470 系列容量已按官方 Product Brief 实证：200MHz、Flash 512~3072KB、SRAM 256~768KB（最高配 3MB Flash + 768KB SRAM）。

## 常见坑

- **以为编 GD32 要装"GD32 专用工具链"**：不需要。GD32F4xx 是 Cortex-M4F，与 STM32F407 同内核同 ABI，xPack arm-none-eabi-gcc 原样复用，只多一个 `-DGD32F450`。
- **拿 STM32 的 CMSIS 头文件去编 GD32**：基址凑巧相同（GPIOF 都是 0x40021400），但 RCU 叫 RCU、寄存器名也不同，用错头文件会编过但跑飞。GD32 工程必须用 `gd32f4xx.h`。
- **把官方库 `.c` 全链接进来却说"寄存器级"**：本站教学工程不 `-I`、不链接官方库 `.c`，main.c 手写访问。链接官方库是另一条路线（库函数级），别混着说。
- **漏 `-DGD32F450`**：不定义型号宏，`gd32f4xx.h` 顶部的容量/中断分支拿不到默认值，编译可能报错或编出错的向量表。
- **照抄官方 `system_gd32f4xx.c` 的 `while(1)` 死等**：晶振不来就死机，G1 已点名这是官方 demo 的坏习惯，教学工程要改成超时回退。

## 短自测

1. 编 GD32F450 需要换一套新的交叉编译器吗？为什么？
2. 官方固件库 V3.3.3 的两层结构各叫什么？各举一个代表文件。
3. G1 工程的 Makefile 里，哪一组编译旗和 STM32 工程逐字相同？哪一个是 GD32 专属？
4. 本站 GD32 工程是"寄存器级"，那官方库 `.h` 文件在这个工程里扮演什么角色？
5. `system_gd32f4xx.c` 和 ST 的 `system_stm32f4xx.c` 在"上电默认频率"上有什么差别？

<details><summary><b>参考答案（先自己想完再展开）</b></summary>

1. 不需要。GD32F4xx 是 ARM Cortex-M4F，与 STM32F407 同内核、同 FPU（FPv4-SP-D16）、同硬浮点 ABI。xPack arm-none-eabi-gcc 的 target 是 ARM 体系（`arm-none-eabi-` 的 `arm`），与芯片厂无关。芯片厂差异在外设寄存器，由 CMSIS 设备头文件描述，不归编译器管。
2. 两层：**CMSIS 设备层**（代表 `gd32f4xx.h`、`system_gd32f4xx.c`，描述"这颗芯片"：基址、中断号、上电时钟初始化）与**标准外设库层**（代表 `gd32f4xx_rcu.h/.c`、`gd32f4xx_gpio.h/.c`，每个外设一对，给寄存器位定义 + 库函数）。
3. `-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard` 与 STM32 工程逐字相同（这四件描述 Cortex-M4F 内核，与芯片厂无关）。GD32 专属的是 `-DGD32F450`：型号选择宏，挑 Flash/RAM 容量与中断向量条数。
4. 当**事实字典**读：写代码时打开 `.trellis/ref/gd32/gd32f4xx.h`，查寄存器偏移与位名，抄进 main.c 的 `#define`，并在注释里挂头文件行号凭证。`.h` 不进编译（不 `-I`），main.c 手写 `*(volatile uint32_t*)` 访问。
5. GD32 的 `system_gd32f4xx.c` 里 `SystemInit()` 把 PLL 直接拉到 **200MHz**（F450 官方默认档，PSC25/N400/P2/Q9）；ST 的 `system_stm32f4xx.c` 默认留在 **168MHz**。另外 GD32 官方文件**不设 Flash 等待周期**（FMC_WS 全文检索零命中），这是 G1 第四节点名的"官方留白"。

</details>

## 对照表：本章概念 → 仓库落点

| 本章说的 | 仓库里哪一行 |
|---|---|
| 工具链零增量、`-DGD32F450` | [code/gd32/01-rcu-clock/Makefile:5-11](https://github.com/zhuguang-ZFG/STM32/blob/main/mcu/code/gd32/01-rcu-clock/Makefile) |
| 启动文件（GCC 版向量表 + Reset_Handler） | code/gd32/01-rcu-clock/startup_gd32f4xx.s:15-40 |
| 链接脚本（Flash 0x08000000 / SRAM 0x20000000） | code/gd32/01-rcu-clock/gd32f4xx.ld |
| 寄存器级手写访问 + 行号凭证 | code/gd32/01-rcu-clock/main.c:23-35 |
| 官方库 V3.3.3 版本锚 | .trellis/ref/gd32/gd32f4xx_gpio.h:5（`V3.3.3`） |
| CMSIS 设备头（基址总线挂载） | .trellis/ref/gd32/gd32f4xx.h:305-357（@10d02f4） |
| system 文件（200MHz 时钟树初始化） | .trellis/ref/gd32/system_gd32f4xx.c:936-1003（G1 全章解剖） |

## 你做到了

- 工具链从"还要再装一套吗"变成"零增量复用"：GD32F4xx 和 STM32F407 是同一个 Cortex-M4F 内核；
- 官方固件库 V3.3.3 的两层结构（CMSIS 设备层 + 标准外设库层）不再是一坨乱文件，每个 `.h` 都能归类；
- 知道本站 GD32 工程是"读 `.h` 当字典、手写访问"，下一章 G1 的每个魔法数字你都能在 `.trellis/ref/gd32/` 里查到出处。

开箱对上：startup_gd32f4xx.s 管向量表，Reset_Handler 里开 FPU、拷 .data、清 .bss 再进 main；system_gd32f4xx.c 把时钟树拉到 200MHz；gd32f4xx.ld 划地盘，Flash 起始 0x08000000、SRAM 起始 0x20000000。行李是零：同为 Cortex-M4F，B0 装好的那套 xPack arm-none-eabi-gcc 直接复用，旗逐字相同，只添 -DGD32F450 一个宏。往后每一章查偏移、查位名，花的都是这份零行李红利。

<div class="achievement">
✅ 下一站：<a href="01-rcu-clock.html">G1 RCU 时钟树</a>：200MHz 是怎么算出来的，与 STM32F4 的 RCC 逐字段对照。
</div>

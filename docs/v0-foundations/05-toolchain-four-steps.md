---
title: "工具链与四步构建"
platforms: [generic]
---

# 工具链与四步构建

> 电脑是 x86，芯片是 ARM。你按下的每一次编译，都是一群程序在替另一块芯片准备口粮。本章把“一行 C 变成 Flash 里的一串字节”拆成可检查的几件事：谁在运行、谁在干活、库从哪来、四步各留下什么、ELF 怎么读，以及第一次装环境要验收哪五步。

## 本章罗盘

- **问题**：`arm-none-eabi-` 三段各管什么，为什么系统 `gcc` 编不了 F407？`gcc` 自己不做编译，它把活分给谁？`-E`、`-S`、`-c` 和链接各留下什么文件，报错时怎样一眼看出死在哪个阶段？ELF 头的五个字段与节表各自回答什么问题？裸机没有 Linux 系统调用，`printf` 的输出凭什么能接到串口？第一次装工具链、make、OpenOCD、ST-Link 驱动和 SWD 线，每一步验收什么？
- **交付**：能用 build/host/target 说明“交叉”交叉在哪；能按 binutils 的分工查符号、段、体积与格式；能说清 newlib 钩子如何把 `printf` 接到串口；能用 `gcc -###` 读出 cc1、as、collect2 的调度链；能亲手跑完四步并在 `.i`、`.s`、`.o`、`.elf` 里找到对应证据；能读 ELF 头五字段与节表的 `Addr`/`Off`/`Size`/`Flg`；能按五步搭好环境，并用三条命令确认自己用的是哪套工具链。
- **边界**：本章以 Cortex-M 裸机、F407 工程与 xPack GNU Arm Embedded GCC 15.2.1 的来源记录为证据，概念适用于没有 OS 的 ARM 嵌入式工程。链接脚本、启动文件与 map 体积审计留给[第 6 章](./06-linker-startup-map.md)；Makefile 与遗留构建栈留给[第 7 章](./07-build-systems-legacy.md)；GDB 与 SWD 调试留给[第 20 章](../v2-reliability/20-debug-performance.md)；寄存器与外设地址留给[第 8 章][ch08]及后续驱动章。环境五步以 Windows 10/11 为主线，Linux 与 macOS 只给对应命令名；板上烧录与点灯步骤来源没有记录本机复跑，本章明确标为未跑。
- **依据锚点**：B0《工具链全景：四个软件一台戏》（`mcu/docs/build/00-toolchain.md`）、B1《四步构建：从 main.c 到机器码》（`mcu/docs/build/01-four-steps.md`）、B2《ELF 解剖：把固件放上解剖台》（`mcu/docs/build/02-elf.md`）、S0《环境搭建：裸机工具链》（`mcu/docs/stm32/00-env.md`）；根书第 01 章《开发环境搭建》（`docs/01-开发环境搭建.md`）的 SWD 接线与 ST-Link 驱动部分。工具链版本、四步读数、ELF 数字均转引自上述来源。

## 先做出来

这一节不需要开发板，只需要 `arm-none-eabi-gcc` 已经在 `PATH` 里。工具链还没装，先跳到后面的“环境搭建五步”，装完再回来。

先看四步构建留不留下证据：

```bash
cd mcu/code/toolchain/01-four-steps
sh probe.sh steps
```

跑之前押两个数字：65 行的 `main.c` 预处理后会膨胀到多少行，汇编又会到多少行？再押第三个：链接前 `.text` 的地址栏是多少，链接后它落在哪里？

来源取证机的输出是：`main.i` 1575 行、`main.s` 3757 行；`.o` 里的 `.text` 地址栏是 `00000000`，链接后 `.text` 从 `0x08000188` 开始。前两个数说明头文件与宏的体量，第三个数说明“可重定位”到底是什么意思。

再看调度员怎样把活分包：`arm-none-eabi-gcc -### -c -mcpu=cortex-m4 -mthumb main.c -o main.o` 会打印 `cc1.exe` 与 `as.exe` 两行（路径已截断）。一条 `-c` 命令调用了两个程序：`cc1` 先把 C 变成汇编，`as` 再把汇编变成目标文件。加上 `-###` 只打印、不执行，正好用来核对“我以为它在干什么”和“它实际调用了谁”。

## 机制

### 三胞胎：build、host、target

先把整条路收进一张图：源码在 PC 上被工具链加工成 `blink.bin`，再经 OpenOCD 与 ST-Link 落进 F407 的 Flash。

![交叉编译工具链全景：从 main.c 到 F407 Flash 的完整路径](/arch/toolchain-pipeline.png)

GCC 用三个词描述“谁在哪台机器上干什么”：

| 角色 | 回答的问题 | 本章取值 |
| --- | --- | --- |
| build | 工具链在哪种机器上被构建 | x86-64 PC |
| host | 编译器在哪种机器上运行 | x86-64 PC |
| target | 编译器为哪种机器产码 | ARM Cortex-M4 |

来源把 build 与 host 简化成“编译器自己跑在哪、产出的编译器跑在哪”。对官网下载的预编译工具链，这两个角色通常都是同一台 x86-64 PC，简化不影响判断；真正决定你能否编出固件的是 **target**。

普通 PC 开发里 build = host = target = x86，叫本机编译。嵌入式里 build = host = x86、target = ARM，叫交叉编译：运行编译器的机器，与运行编译产物的芯片，不是同一个体系。`arm-none-eabi-gcc` 就是 target 为 ARM 的交叉 gcc：它跑在你的 PC 上，吐出的却是 Cortex-M4 能执行的机器码。

为什么不能直接用系统 `gcc`：系统 gcc 的 target 是 x86-64，产出 x86 指令，F407 的 ARM 内核不认识。必须装一套 target=arm 的交叉工具链。前缀就是区分本机版与交叉版的工牌：

- `arm`：arch，ARM 体系；
- `none`：vendor，无特定厂商；
- `eabi`：ABI，嵌入式应用二进制接口，面向没有 OS 的裸机。

对照 `arm-linux-gnueabihf-`：它面向跑 Linux 的 ARM，链接的是 Linux 那套启动文件与 C 库；拿它编裸机，库和入口都对不上。

来源取证用的版本是 **xPack GNU Arm Embedded GCC 15.2.1**（取证记录里的安装路径是解压目录 `xpack-arm-none-eabi-gcc-15.2.1-1.1/bin`，盘符随解压位置而定），与 CI 的 arm-host job 同源；宿主侧是 **MinGW-Builds gcc 16.1.0**（x86-64）。F407 的交叉编译旗是 `-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard`。版本号会变，target 与 ABI 的对应关系不会变。

### 兵器谱：七件主兵器加两件量具

`gcc` 是调度员，真正动手的是 binutils。来源的兵器谱标题写“七件兵器”，表里另外还列了两件查看用的量具。七件主兵器各有一招：

| 工具 | 一招鲜 | 在本章哪里出现 |
| --- | --- | --- |
| `as` | 汇编器：把 `.s` 汇编成 `.o` | 四步的第 3 步、`-###` 的第二行 |
| `ld` | 链接器：把 `.o` 与库合成 `.elf` | 四步的第 4 步，链接脚本章 |
| `ar` | 归档：把多个 `.o` 打成 `.a` 静态库 | 库的打包形式 |
| `nm` | 符号表：列出 `.elf` 里的符号与地址 | 查 `U` 符号、查 `main` 与弱符号 |
| `objcopy` | 格式转换：`.elf` 转 `.bin`/`.hex` | 烧录产物 |
| `objdump` | 反汇编与段信息：`.elf` 转汇编、列节表 | 查 `.text` 大小与地址 |
| `readelf` | ELF 头、节表、程序头，比 objdump 更专 | 本章的 ELF 解剖 |

另外两件是 `size` 与 `strings`：`size` 给 `text/data/bss` 三列体积，`strings` 抽固件里的字面量。它们不参与构建，只参与查看。

记住一条分工：**读固件大部分靠 binutils**。gcc 负责“写出来”，binutils 负责“看清楚”。`objdump -d` 反汇编、`nm -n` 按地址排符号、`readelf -S` 看节、`size` 看体积，这四把刀是嵌入式工程师的日常。

### newlib 与钩子：printf 的出口

PC 上的 C 标准库由 glibc 提供。glibc 依赖 Linux 系统调用，裸机没有 OS，没有 `write()`，`printf` 的“输出”没有现成的去处。

**newlib** 也是 C 库，但面向裸机与嵌入式。它把依赖具体系统的工作抽成一组**钩子函数**：库调用这些函数，底层实现由你补。上层仍然是同一份 `printf`/`malloc` 代码，底层才处理串口输出、堆空间这些具体问题。

| 钩子 | 干什么 | 来源里的实现落点 |
| --- | --- | --- |
| `_write(int fd, char *buf, int len)` | 写一段字节流到“文件描述符” | 串口章把 `printf` 接到 USART |
| `_sbrk(ptrdiff_t incr)` | 给 `malloc` 增长堆 | 链接脚本预留堆空间 |
| `_close/_lseek/_read/_isatty` | 文件操作占位 | 裸机一般空实现 |
| `_exit/_kill/_getpid` | 进程占位 | 裸机一般空实现 |

以 `printf` 为例：newlib 不替你决定“输出到哪”。你实现 `_write`，把收到的字节写进 UART 寄存器，`printf` 就走串口；也可以把输出接到 SWO，经 ITM 送出；或接到 Semihosting，经调试器送回 PC。上层代码不变，变的只是钩子的实现。这就是串口章里 printf 重定向的全部机关。

一个版本坑先记在这里：老版 newlib 默认不带浮点 `printf`，`%f` 可能不工作，需要在链接时加 `-u _printf_float`。这不是语法错误，编译阶段不会提醒你。

### gcc -###：把调度剧本念出来

`arm-none-eabi-gcc` 本身不编译代码。它读参数、查文件后缀，再 fork 出真正干活的工具。加上 `-###` 后，它**只打印将要调用的工具，不执行编译**。看每行开头的程序路径，再看输入输出文件，就能对上分工（来源记录，路径已截断）：

```text
$ arm-none-eabi-gcc -### -E -mcpu=cortex-m4 -mthumb main.c -o main.i
 ".../libexec/gcc/arm-none-eabi/15.2.1/cc1.exe" ... -E ... -o main.i

$ arm-none-eabi-gcc -### -c -mcpu=cortex-m4 -mthumb main.c -o main.o
 ".../libexec/gcc/arm-none-eabi/15.2.1/cc1.exe" ... -o /tmp/ccXXXX.s
 ".../arm-none-eabi/bin/as.exe" ... -o main.o

$ arm-none-eabi-gcc main.o startup.o -T stm32f407xx.ld -o blink.elf
 ".../libexec/gcc/arm-none-eabi/15.2.1/collect2.exe" ...
```

四条事实：

1. **预处理不是独立程序**。老教程说的 `cpp` 只是个壳，现代 GCC 里预处理和编译都是 `cc1`，靠 `-E`/`-S` 开关切换输出。
2. `-c` 这条命令实际调用了**两个**工具：`cc1` 先编译，`as` 再汇编。命令可以写在一起，但两道工序各有产物，不能当成同一步。
3. 链接由 `collect2` 代理：它负责收拾构造函数表（`__libc_init_array` 之类）再调 `ld`。所以链接报错里署名 `ld.exe`。来源记录的链接命令在快照里省略了 `-###`，你自己跑时加上它，就能看到同一行 `collect2`。
4. `-###` 还会打印 `COMPILER_PATH`/`LIBRARY_PATH`。找不到 `-lm`，或怀疑混用了不同版本的库时，先检查这两行指向的路径。

不想逐条敲命令，可以用 `-save-temps` 保留中间产物：它会把 `.i/.s/.o` 自动留在当前目录。查看这些文件，就能回头检查每道工序。

### 四步：E、S、c、链接

![四步构建流水线动画：预处理、编译、汇编、链接各留下什么](/anim/build-four-steps.svg)

#### 第 1 步：预处理 `-E`——宏在纸上摊平

`-E` 只做三件事：展开 `#include`、替换宏、按条件编译裁剪。输出仍是 C 源码，带 `# 行号 "文件"` 标记，给调试器认行用。

```bash
arm-none-eabi-gcc -E main.c -o main.i
```

来源实测：**65 行 → 1575 行**。多出来的 1510 行是 `#include <stdint.h>` 等头文件的内容。打开 `main.i` 找 `main`，第 1556 行的签名没变，但宏全没了。

源码里的 `RCC_BASE` 在 `main.i` 第 1533 行还留着一个 `#define`，但用到它的地方已经摊成纯算术式：

```c
/* main.i 第 1559 行：源码里那行 RCC->AHB1ENR |= RCC_AHB1ENR_GPIOFEN; */
(*(volatile uint32_t *)(((0x40000000UL + 0x00020000UL) + 0x3800UL) + 0x30UL)) |= (1UL << 5);
```

这就是“宏只是文本替换”的实物：地址加法与移位留给编译器做常量折叠，指针、`volatile`、位运算的语义在这一行已经确定。后面两步只是“翻译”它。查展开结果要看**使用处**，不是找那一行 `#define`。

#### 第 2 步：编译 `-S`——C 变成汇编

`-S` 让 `cc1` 停在汇编层。它做语法检查、类型检查、优化，然后吐出目标架构的汇编：

```bash
arm-none-eabi-gcc -S main.i -o main.s      # 来源实测 3757 行
```

`main` 的开场（来源实测节选）：

```asm
main:
	push	{r7, lr}          @ 函数序言：压栈保存返回地址
	add	r7, sp, #0
	ldr	r3, .L6
	ldr	r3, [r3]           @ 读 RCC->AHB1ENR（volatile：必须真读）
	ldr	r2, .L6
	orr	r3, r3, #32        @ 32 = 1<<5 = GPIOFEN
	str	r3, [r2]           @ 写回 RCC->AHB1ENR
```

- `orr r3, r3, #32`：源码的 `|= (1UL << 5)` 被常量折叠成 `#32`。**读-改-写**在汇编里看得一清二楚：先 `ldr` 读、再 `orr` 改、最后 `str` 写。
- 为什么不是一条原子指令？因为 C 里写的就是 `|=`；想避免翻车，要在外设侧换原子入口，这条边界在[第 2 章](./02-c-volatile-ub.md)已经讲过。
- 地址 `0x40023830` 没出现在指令里，而是被塞进字面池（`.L6`），用 `ldr r3, .L6` 取。ARM 的立即数字段装不下 32 位地址，只能这么干。

`-O0` 下函数序言固定存在（`push {r7, lr}` 加 `add r7, sp, #0`，为了调试时栈回溯方便）；换 `-O2` 这两条会消失。优化等级怎样改写汇编，[第 2 章](./02-c-volatile-ub.md)有完整对照。

#### 第 3 步：汇编 `-c`——半成品 `.o`

```bash
arm-none-eabi-gcc -c main.s -o main.o
```

`.o` 叫**可重定位目标文件**。汇编已经生成机器码，但这些代码最终放在哪个地址，还要等链接时决定。下面分别查符号和节的位置：

```text
$ arm-none-eabi-nm main.o
（一个 U 都没有——外设访问是硬编码地址常量，不需要符号决议）

$ arm-none-eabi-nm startup_stm32f407xx.o | grep ' U '
    U _ebss
    U _edata
    U _estack
    U _sbss
    U _sdata
    U _sidata
    U main

$ arm-none-eabi-objdump -h main.o
  6 .text         000000a8  00000000  00000000  0000007c  2**2
```

`nm` 里的 `U` 表示“未定义符号”：本文件用到了这个名字，定义却在别处，要等链接器补地址。`main.o` 一个 `U` 都没有，因为这里访问外设用的是硬编码地址常量；`startup_stm32f407xx.o` 的 `U` 则在列出它还缺哪些定义：`_sidata`/`_sdata`/`_edata`/`_sbss`/`_ebss`/`_estack` 来自链接脚本，`main` 由应用提供。

`objdump -h` 的地址栏 `00000000` 不是最终运行位置。`.text` 此时是个 0xa8 字节的块，链接时才决定把它放到哪里，这就是“可重定位”。查 `nm` 时先认三种符号类型：`T/t` 是代码段（大写全局、小写局部），`U` 是还要去别处找定义，`W` 是弱符号、可以被覆盖。

#### 第 4 步：链接——决议符号，按脚本排座

```bash
arm-none-eabi-gcc main.o startup_stm32f407xx.o \
    -T stm32f407xx.ld -nostartfiles -o blink.elf
```

链接器 `ld` 做两件事：**符号决议**，给每个 `U` 找到定义；**重定位**，按链接脚本安排各段位置，并填入代码需要的地址。来源实测：

```text
$ arm-none-eabi-objdump -h blink.elf
Idx Name          Size      VMA       LMA
  0 .isr_vector   00000188  08000000  08000000    ← 向量表钉在 Flash 起始
  1 .text         0000010c  08000188  08000188    ← 代码紧随其后
  2 .data         00000000  20000000  20000000    ← 变量在 RAM（0x2000_0000）
  3 .bss          00000000  20000000  08000294

$ arm-none-eabi-size blink.elf
   text    data     bss     dec     hex
    660       0    1536    2196     894

$ arm-none-eabi-nm -n blink.elf | grep -E ' (Reset_Handler|main)$'
080001aa T main
08000230 W Reset_Handler
```

- **VMA（Virtual Memory Address）** 是运行时的地址。`.isr_vector` 与 `.text` 在 `0x0800_0000` 段（Flash），`.data`/`.bss` 在 `0x2000_0000` 段（SRAM）。这是链接脚本把“哪块东西放哪块存储”焊死的效果，[第 6 章](./06-linker-startup-map.md)整章讲这个。
- `text 660` = 392（向量表）+ 268（代码）。`bss 1536` 是 `._user_heap_stack` 预留的栈与堆空间，不占 Flash。
- `Reset_Handler` 是 **W（弱符号）**：启动文件里给了默认实现，用户可以覆盖。芯片复位后 CPU 从 `0x0800_0000` 取向量表第 2 个字跳到这里。
- `main` 的地址按 `nm` 口径记为 `080001aa`：`nm` 把 Thumb 位抹掉了，给出纯地址。换 `readelf -s` 问同一个符号，会显示 `080001ab`——**`readelf -s` 保留这一位，`nm` 抹掉它**。那一位 1 是 Cortex-M 只跑 Thumb 的标记，不是错位。断点用纯地址，往向量表或函数指针里填地址时用带 1 的形式。

四道工序走完，一份 65 行的 C 源码变成了能烧进 Flash 的 `.elf`。每一步都留下可检查的中间文件：`.i`（纯 C）、`.s`（汇编）、`.o`（可重定位目标）、`.elf`（可执行）。

### ELF：头五字段与节表

![ELF 节表与程序头双重视角动画：同一份固件的两套目录](/anim/elf-sections.svg)

#### 头五字段：先回答“我是谁”

来源标本 `elf_probe.elf` 的 ELF 头：

```text
  Magic:   7f 45 4c 46 01 01 01 00 00 00 00 00 00 00 00 00
  Class:                             ELF32
  Type:                              EXEC (Executable file)
  Machine:                           ARM
  Entry point address:               0x8000189
  Number of program headers:         2
  Number of section headers:         20
```

五个字段一次说完：

- **`Magic: 7f 45 4c 46 ...` / `Class: ELF32` / `Type: EXEC`**：前四字节是 `0x7F` 加 `'E' 'L' 'F'` 的签名，第五字节 `01` 表示 ELF32，第六字节 `01` 表示小端；`EXEC` 是可执行文件，不是共享对象，也不是 PIE。裸机没有动态链接器，也没有 ASLR，地址从链接那一刻就定死了。
- **`Machine: ARM`** 与头里的 `Flags: 0x5000400, Version5 EABI, hard-float ABI`：这一行是“我用的是硬浮点 ABI”的官方声明。编译选项与库的 ABI 对不上时，症状可能是链接通过、跑起来浮点全错，第一个该查的就是这里。
- **`Entry point address: 0x8000189`**：CPU 复位后不看这个字段（它看向量表），但 GDB 的 `load` 与 `break *0x8000189` 看它。
- **`Number of program headers: 2` 与 `section headers: 20`**：两套目录各有几项。2 与 20 不相等这件事，就是节表与程序头分工的全部内容。

顺手把“差 1”钉死：来源标本的 `nm` 显示 `08000188 W Reset_Handler`，而 ELF 入口是 `0x8000189`。`0x08000188 | 1 = 0x08000189`。**最低位是 Thumb 状态位，不是地址位**。往向量表和函数指针里填地址时必须带 1，工具之间对照时先抹平。

#### 节表：链接器的抽屉

来源里 `blink.elf` 的节表：

```text
  [ 1] .isr_vector  PROGBITS  08000000 001000 000188 00   A
  [ 2] .text        PROGBITS  08000188 001188 00010c 00  AX
  [ 3] .data        PROGBITS  20000000 001294 000000 00  WA
  [ 4] .bss         NOBITS    20000000 000000 000000 00  WA
  [ 5] ._user_heap_stack NOBITS 20000000 002000 000600 00   WA
```

读表时分别问：运行时放哪、在文件里放哪、占多少字节、是什么类型、带什么标志。

- **`Addr`（VMA，运行地址）**：先用这一列判断这个节运行时位于哪块存储器。`0x08000000` 属于 Flash，`0x20000000` 属于 RAM。blink 的 `.data`/`.bss`/`._user_heap_stack` 都写着 `0x20000000`，前两个大小为 0，所以堆栈段直接从 RAM 起始位置开始。
- **`Off`（文件偏移）**：这个节在 `.elf` 文件里的第几字节。`.text` 的 `Addr=0x08000188` 而 `Off=0x001188`，差 `0x1000`。第一个节要到文件第 `0x1000`（4096）字节才开始，前面 4096 字节里只装了 52 字节的 ELF 头和 64 字节的程序头，剩下是对齐垫子。别把文件偏移当内存地址。
- **`Size`**：以字节计的大小。`0x188` = 392，也就是 98 个 4 字节表项；到 `startup_stm32f407xx.s` 的 `g_pfnVectors` 里能数出同样的条数：栈顶、复位入口，以及其余异常与中断入口。
- **`Type` 与 `Flg`**：`PROGBITS` 表示文件里有货，`NOBITS` 表示只登记不给货。`.bss` 是 `NOBITS`，`Off` 甚至是 `000000`，文件里没有它的位置，只有一张“请清零”的便条。`Flg` 里的 `A`（alloc）是最重要的一列：没有 `A` 的节，烧录时与你无关。

`blink.elf` 有 20 个节，带 `A` 的只有 5 个。剩下 14 个是给人看的说明书：`.symtab`、`.strtab`、`.shstrtab`、`.comment`、`.ARM.attributes`，以及 9 个 `.debug_*`。5 个 alloc 节里，`.data` 大小 0、`.bss` 与 `._user_heap_stack` 是 `NOBITS`，真正在文件里占字节的只有 `.isr_vector` 与 `.text` 两个。392 + 268 = 660 字节，正好是 `size` 的 `text` 列，也正好是 bin 的体积。

```text
   text   data   bss   dec   hex   filename
    660      0  1536  2196   894   build/blink.elf
```

`blink.elf` 文件本身是 34,604 字节，`objcopy -O binary` 之后只剩 660 字节。34,604 − 660 = 33,944 字节，全是调试信息与符号表。这也是为什么“烧 bin 才谈第几字节”。

节表回答“文件里有哪些抽屉”，程序头回答“装载器怎样装车”。`blink.elf` 的两条 `LOAD` 把 `.isr_vector` 与 `.text` 装进 `0x08000000`（`FileSiz=MemSiz=0x294`），把 `.bss` 与堆栈预留区装进 `0x20000000`（`FileSiz=0`，`MemSiz=0x600`）；它的 `.data` 是空的，看不出差值。来源另一具标本 `elf_probe.elf` 的 `.data` 有初值，第二条 `LOAD` 是 `FileSiz=0x0c`、`MemSiz=0x20`，差的 20 字节正是 `.bss`：有初值才占 Flash，为 0 只占 RAM，在 ELF 里就是这两个数的差。VMA 与 LMA 的完整故事在[第 6 章](./06-linker-startup-map.md)。

### 环境搭建五步

![环境搭建五步闭环：交叉编译器、make、OpenOCD、ST-Link 驱动、SWD 接线](/anim/env-setup-flow.svg)

来源有两块板：S0 的野火 F407 霸天虎，根书第 01 章的 F103C8 BluePill。五步的验收命令相同，接线脚号按板子对号，不要混用。霸天虎不板载仿真器，必须自备 ST-Link V2 或兼容的 J-Link/DAP；板载 RGB 灯在 PF6/7/8。

![基于 STM32F407 的第三方开发板，LQFP100 封装](/images/boards/stm32f407-board.jpg)

> F407 家族板卡形态参考：图为一块第三方 F407 板（LQFP100）；来源的基准板霸天虎为 F407ZGT6（LQFP144），外观不同、芯片同门（Wikimedia Commons，CC0，作者 Ordercrazy）。

**第一步：装 ARM 交叉编译器。** 打开 Arm 官网开发者页，搜 “Arm GNU Toolchain”，下载 Windows 版 `arm-gnu-toolchain-14.x.rel*-mingw-w64-x86_64-arm-none-eabi.exe`。安装到最后一步务必勾选 “Add path to environment variable”，然后开一个**新的**终端用 `arm-none-eabi-gcc --version` 验证。来源环境章以 14.x 安装包为例，看到 `gcc version 14.x.x` 即成功；本书取证工程的版本是 15.2.1。版本号会变，验收点不变：`--version` 要报出 `arm-none-eabi` 目标。

**第二步：装 make。** Windows 没有自带 make，最省心的来源是 **xPack Windows Build Tools**：下载 `xpack-windows-build-tools-*-win32-x64.zip`，解压到无中文无空格的路径（如 `D:\tools\xpack-build-tools`），把其 `bin` 目录加入系统 PATH，新开终端用 `make --version` 验证。

**第三步：装 OpenOCD。** 下载 **xPack OpenOCD** 的 Windows 版 zip，解压到无中文无空格的路径，`bin` 加入 PATH，用 `openocd --version` 验证。OpenOCD 一边通过 USB 跟 ST-Link 说话，一边通过 SWD 跟芯片说话，把 `program` 命令翻译成对 Flash 的擦写。SWD 只有两根信号线：SWDIO（数据）与 SWCLK（时钟）。完整调试链在[第 20 章](../v2-reliability/20-debug-performance.md)。

**第四步：装 ST-Link 驱动。** 正版 ST-Link / ST-Link V2 装 ST 官方的 **STSW-LINK009** USB 驱动；DAPLink（CMSIS-DAP）在 Windows 10/11 上免驱。插上仿真器，设备管理器里应出现 “STM32 STLink” 或对应设备，没有黄色感叹号。固件太旧时报 DFU 相关错误，用 ST-Link Upgrade 升级后再连。

**第五步：SWD 接线。** 霸天虎的 SWD 座按下表连接：

| ST-Link | 开发板 SWD 座 | 说明 |
| --- | --- | --- |
| SWDIO | SWDIO | 数据 |
| SWCLK | SWCLK | 时钟 |
| GND | GND | 必须共地 |
| 3.3V | 3.3V | 仅作检测，不给板子供电 |

板子用自己的 USB 供电，仿真器的 3.3V 只接检测脚。两路电源对供是烧板的经典姿势。F103C8 的脚号是：SWDIO 在 PA13（LQFP48 第 34 脚），SWCLK 在 PA14（第 37 脚），NRST 在第 7 脚，BOOT0 在第 44 脚；第 35 脚是 VSS_2、第 36 脚是 VDD_2，数脚时别把第 35 脚当成 SWCLK。CubeMX 的 SYS Debug 必须选 Serial Wire，否则 PA13/PA14 会被配成普通 GPIO，烧一次后就再也连不上。

五步完成后，用构建做一次总验收：

```bash
cd mcu/code/stm32/00-blink
make
```

产物有四个：`blink.elf` 带调试信息，GDB 用它；`blink.bin` 是纯二进制镜像；`blink.hex` 是 Intel HEX；`blink.map` 是符号地址清单。烧录命令是 `make flash`，来源描述的关键日志是 `** Programming Started **`、`** Verified OK **`、`** Resetting Target **`，随后 PF6 红灯约 1 Hz 闪烁。**来源没有记录本机板上复跑，本章只把它标为待上板验证，不把点灯现象当成已复现的实测。**

## 测量与证据

本章数字来自 B0、B1、B2 与 S0 的取证记录。四步与 ELF 的读数由来源工程在 xPack GNU Arm Embedded GCC 15.2.1 上跑出；环境五步中，`--version` 类检查是来源给出的验收命令，板上烧录与点灯没有本机复跑记录。换工具链版本、换优化档或换板子，具体数字会变，判读方法不变。

| 取证项 | 来源命令 | 来源记录里的读数 |
| --- | --- | --- |
| 预处理与汇编体量 | `sh probe.sh steps`（01-four-steps） | `main.c` 65 行 → `main.i` 1575 行，`main.s` 3757 行 |
| 目标文件 `.text` | `arm-none-eabi-objdump -h main.o` | `000000a8`、地址 `00000000` |
| 链接后 `.text` | `arm-none-eabi-objdump -h blink.elf` | `0000010c`、VMA `08000188` |
| 体积汇总 | `arm-none-eabi-size blink.elf` | text 660、data 0、bss 1536、dec 2196、hex 894 |
| 符号与弱符号 | `arm-none-eabi-nm -n blink.elf` | `080001aa T main`、`08000230 W Reset_Handler` |
| ELF 头 | `sh probe.sh head`（02-elf） | ELF32、EXEC、ARM、入口 `0x8000189`、程序头 2、节头 20 |
| 向量表与 Thumb 位 | `readelf -h` 与 `nm` 对照 | `0x8000189` 与 `08000188` 差 1 |
| 节表分配 | `readelf -S` / `objdump -h` | `.isr_vector` 392 字节、`.text` 268 字节、5 个 alloc 节 |
| 文件与镜像体积 | `ls -l` 与 `objcopy` | `blink.elf` 34,604 字节，bin 660 字节，差 33,944 字节 |
| 程序头 | `readelf -l` | 两条 `LOAD`；`.data` 空；`FileSiz` 与 `MemSiz` 的差由 `.bss` 解释 |
| 调度链 | `arm-none-eabi-gcc -### -c` | `cc1.exe` 与 `as.exe` 各一行；链接由 `collect2.exe` 代理 |
| 报错阶段 | `sh probe.sh errors` | 预处理 `fatal error`、编译 `error: expected`、链接 `undefined reference` |
| 工具链自查 | `--version` / `where` / `-print-search-dirs` | 来源给命令与判据，未记录本机输出 |

判断“真的会了”：给你一条编译报错，能在十秒内按关键字报出阶段；给你一个 `.elf`，能用五条命令说清入口、Flash 占用、RAM 占用与某个符号的住址；给你一条 `-###` 输出，能指出哪一行是 `cc1`、哪一行是 `as`、哪一行是 `collect2`；给你一套刚装好的环境，能用 `--version`、`where`、`-print-search-dirs` 证明“我到底在用哪套工具链”。

## 失败分支

| 现象 | 原因 | 区分证据 | 下一动作 |
| --- | --- | --- | --- |
| `'arm-none-eabi-gcc' 不是内部或外部命令`，或版本不是你以为的那套 | PATH 没生效，或官方版与捆绑版混装 | 重开终端仍报错；`where arm-none-eabi-gcc` 排第一的路径 | 安装时勾 Add path，或调整 PATH 只保留一套 |
| 编译裸机报启动文件/库错误 | 用了 `arm-linux-gnueabihf-gcc` | 前缀与搜索路径指向 Linux 工具链 | 换 `arm-none-eabi-`，清掉旧的构建目录 |
| `fatal error: no_such_header_xyz.h: No such file or directory` | 预处理阶段找不到头文件 | `fatal error` 只在预处理出现 | 补 `-I` 或把头文件放对位置 |
| `error: expected expression before ';' token` | 编译阶段语法或类型错误 | 报错带精确行列号 | 改源码语法，不是补库 |
| `undefined reference to 'SystemInit'` | 链接阶段缺符号 | 编译已全部通过；可能附带 `cannot find entry symbol Reset_Handler` | 补定义、补 `.o` 或补启动文件，不是改语法 |
| `objdump -h main.o` 地址是 0 | `.o` 是可重定位文件 | `.o` 地址栏恒为 0，`.elf` 才有最终地址 | 查 `.elf`，不要拿 `.o` 对地址 |
| 汇编 `.s` 时报 MCU 参数错误 | 汇编也走 gcc 调度，漏了 `-mcpu`/`-mthumb` | 命令里是否带交叉编译旗 | 补齐旗标再汇编 |
| `printf("%f")` 不输出或输出乱码 | 老版 newlib 默认不带浮点 printf | 编译链接都通过，只有运行期不对 | 链接时加 `-u _printf_float` |
| `make: *** missing separator` | 命令行首用了空格 | 编辑器是否把 Tab 换成空格 | 行首改成 Tab |
| OpenOCD 报 `Error: open failed` 或找不到 ST-Link | 驱动未装，或杜邦线虚接 | 设备管理器有无 “STM32 STLink” | 先查第四步驱动，再重插 SWD 线 |
| 烧录成功但灯不亮 | 引脚号照搬了别的板子 | 霸天虎是 PF6，网上教程常是 PA8/PF9 | 查自己板子的原理图 |
| 仿真器与板子都接 3.3V 后发热或连不上 | 两路电源对供 | 3.3V 是否接到板子的电源脚 | 板子单独 USB 供电，3.3V 只作检测 |
| `.elf` 几十 KB，以为 Flash 装不下 | 把调试信息算进了固件 | `size` 的 text+data 才是 Flash 占用 | 看 `size`，不要看 `.elf` 文件大小 |
| `readelf` 入口与 `nm` 地址差 1 | Thumb 状态位：`readelf` 保留、`nm` 抹掉 | 同一符号两工具对照：`readelf -s` 最低位为 1，`nm` 最低位为 0 | 断点用纯地址；填向量表或函数指针时用带 1 的形式 |

## 离开检查

1. build、host、target 各回答什么问题？为什么系统 `gcc` 编不了 F407？`arm-none-eabi-` 三段各代表什么？
2. binutils 七件主兵器各有一招：`.elf` 转 `.bin` 用谁？反汇编用谁？列符号用谁？看体积用谁？
3. 裸机为什么不能用 glibc？newlib 的 `_write` 与 `_sbrk` 分别解决什么问题？`printf` 想走串口，要动哪一层？
4. `gcc -### -c` 为什么打印两行工具路径？链接时 `collect2` 与 `ld` 是什么关系？
5. 四步各留下什么文件？`main.i` 为什么从 65 行涨到 1575 行？`.o` 的地址栏为什么是 0？`fatal error`、`error:`、`undefined reference` 分别死在哪一步？
6. ELF 头五个字段各说什么？为什么程序头是 2 条而节表有 20 项？节表里的 `A` 标志、`PROGBITS`/`NOBITS`、`FileSiz`/`MemSiz` 各影响什么？
7. 环境搭建五步各验收什么？SWD 四根线怎么接，为什么 3.3V 只作检测？板上点灯步骤为什么标为未跑？

<details>
<summary>对照答案</summary>
1. build 是工具链被构建的机器，host 是编译器运行的机器，target 是编译器产码的目标体系。预编译工具链的 build 与 host 通常都是 x86-64 PC，target 是 ARM Cortex-M4，所以叫交叉编译。系统 gcc 的 target 是 x86-64，产出 x86 指令，F407 不认识。`arm` 是 ARM 体系，`none` 是无特定厂商，`eabi` 是面向裸机的嵌入式 ABI。
2. `.elf` 转 `.bin` 用 `objcopy -O binary`；反汇编用 `objdump -d`；列符号用 `nm`；看体积用 `size`。`as` 负责 `.s` 到 `.o`，`ld` 负责链接，`ar` 负责打静态库，`readelf` 负责 ELF 头、节表与程序头。
3. glibc 依赖 Linux 系统调用，裸机没有 OS，`write()` 不存在。newlib 把系统相关工作抽成钩子：`_write` 决定字节流往哪写，`_sbrk` 给 `malloc` 增长堆。`printf` 想走串口，要实现 `_write`，把字节写进 UART 寄存器；上层 `printf` 不用改。
4. `-c` 同时包含编译与汇编两道工序：`cc1` 先出汇编，`as` 再出 `.o`。链接由 `collect2` 代理，它收拾构造函数表后再调用真正的 `ld`，所以链接报错署名 `ld.exe`。
5. 四步留下 `.i`（预处理后的 C）、`.s`（汇编）、`.o`（可重定位目标）、`.elf`（可执行）。`main.i` 变大是因为 `#include` 的头文件被整份贴入、宏被展开。`.o` 还没分配最终地址，所以地址栏是 0。`fatal error` 在预处理，`error:` 在编译，`undefined reference` 在链接。
6. 头五字段：Magic（签名、ELF32/小端）、Class/Type（ELF32、EXEC）、Machine（ARM 与硬浮点 ABI）、Entry（入口地址，GDB 用）、两套目录的计数。程序头 2 条是装载器的装车批次，节表 20 项是链接器与调试器看的抽屉清单。`A` 表示 alloc，没 A 的节烧录时无关；`PROGBITS` 有文件内容，`NOBITS` 只登记不给货；`FileSiz` 是文件里带的字节，`MemSiz` 是运行时要占的字节，差值由 `.bss` 与启动代码补。
7. 五步：交叉编译器（`arm-none-eabi-gcc --version`）、make（`make --version`）、OpenOCD（`openocd --version`）、ST-Link 驱动（设备管理器无黄色感叹号）、SWD 接线（SWDIO/SWCLK/GND/3.3V 检测）。3.3V 只作检测，板子单独 USB 供电，避免两路电源对供。板上烧录与点灯来源没有记录本机复跑，所以标为未跑。
</details>

动作验收：在自己的机器上装好五步，用 `arm-none-eabi-gcc --version`、`where arm-none-eabi-gcc`（Linux 用 `which`）、`-print-search-dirs` 三条命令写下“我用的是哪套工具链”；再拿一个现成工程跑一遍 `-E`、`-S`、`-c`、链接，把四份中间产物和一条 `readelf -h` 输出留在构建目录里。

[ch08]: ../v1-drivers/08-architecture-memory-clock.md

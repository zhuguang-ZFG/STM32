---
title: B2 ELF 解剖：把固件放上解剖台
status: done
difficulty: 2
minutes: 65
---

# B2 ELF 解剖：readelf 与 objdump 实拆固件

> 🎯 烧进芯片的只有 **660 字节**，可你的 `blink.elf` 有 **34,604 字节**。那 33,944 字节的差额不是 waste，是一整份写给活人看的说明书。本章动五刀，把它读完，每一刀都配本机实测输出。

本章所有数字来自同一套工具链：xPack GNU Arm Embedded GCC **15.2.1 (20251203)**，`-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard -O0 -g3`。版本不同，`.debug_*` 的个数和符号数量会变，**地址与结构关系不会变**。

## 本章精髓

1. **为什么一个文件要装两套目录**：链接器与装载器要查的信息不同，所以 ELF 同时提供两套目录。链接器按**节（section）**分抽屉：`.isr_vector`/`.text`/`.rodata`/`.data`/`.bss` 各归各；装载器按**段（segment，即程序头里的 `PT_LOAD`）**装车，把若干节打包成一批，一次性摆到指定地址。查体积时，先分清是在数文件里的内容，还是芯片要用的内容：blink.elf 的 20 个节里只有 5 个带 `A`（alloc）标记，真正在文件里占字节的只有 2 个。**"34 KB 的固件"和"660 字节的固件"说的是同一件事。**
2. **为什么 VMA 与 LMA 必须分家**：`.data` 在 RAM 中运行，初值存放在 Flash。两个地址由链接脚本规定：`stm32f407xx.ld:91,100` 里的 `_sidata = LOADADDR(.data)` 与 `} >RAM AT> FLASH`，对应到 `elf_probe.elf` 的程序头，就是 `VirtAddr=0x20000000 / PhysAddr=0x08000244`。第三刀会对照两份标本：`blink.elf` 的 `.data` 是空的，同一个位置算出的是 `0x08000294`，不要把两份输出混用。[C1](../c/01-memory-model.md) 解释初值由谁搬、怎样搬；本章则练习**从文件里读出这对地址**。
3. **为什么所有地址都可能差 1**：`readelf -h` 说入口是 `0x8000189`，`nm` 说 `Reset_Handler` 在 `0x08000188`。谁错了？都没错。Cortex-M 只跑 Thumb 态，**最低位是状态位不是地址位**。不懂这条约定，你会在 GDB 里对着一句 "Breakpoint at 0x8000189" 找不到函数。

- **能记住**：ELF 头五个字段各说什么；节表与程序头分别回答谁的问题；`FileSiz` 与 `MemSiz` 的差从哪来
- **能理解**：为什么 `Addr` 与 `Off` 差 `0x1000`；为什么 `nm` 与 `readelf -s` 给出的函数地址差 1；为什么反汇编里会冒出 `MCU.....` 这种"乱码"
- **能用**：拿到任何一颗 MCU 的 `.elf`，五条命令内说清"入口在哪、什么占 Flash、什么占 RAM、每个符号住在第几字节"

## 先修

- [B1 四步构建](01-four-steps.md)：本章拆的是**链接**那一步的产物；[C1 内存模型](../c/01-memory-model.md)：段的双重户籍已在该章建立直觉。
- 想知道"这些地址是谁规定的"→ [B3 链接脚本](03-linker-script.md)；想知道"谁照着这两个地址搬运行李"→ [B4 启动文件](04-startup.md)。

## 先跑起来（10 分钟 quick win，**不用开发板**）

先猜：ELF 里记录的入口地址，和符号表里的复位例程地址，是否相同？再猜它们若不相同，会差多少。运行后找到这两项输出，直接比较。

```bash
cd code/toolchain/02-elf
sh probe.sh head
```

```
Entry point address:               0x8000189
08000000 r g_pfnVectors
08000188 W Reset_Handler
```

`0x8000189` 与 `08000188` 差的那个 **1**，本章第三节会亲手从向量表里再挖出来一次。CPU 复位后读的第一口数据里，写的就是 `0x08000189`。跑不出来别慌，下面五刀每刀都给命令。

## 动画：ELF 的双重视角

看动画时先问两件事：链接器怎样查各个节，装载器怎样查程序头？它们看的都是同一份固件，用的却是两套目录。

![ELF 节表与程序头双重视角动画](/anim/elf-sections.svg)

## 解剖台上的两具标本

| 标本 | 怎么来的 | 为什么请它上桌 |
|---|---|---|
| `build/blink.elf` | `../../stm32/00-blink` 的 `main.c` + `startup_stm32f407xx.s` + `stm32f407xx.ld`，按它 Makefile 里那三条命令原样构建（不依赖 make） | 你已经在 [B1](01-four-steps.md) 见过的真固件；缺点是**太干净**：`.data` 大小 0，VMA/LMA 分家看不全 |
| `build/elf_probe.elf` | 本目录 `elf_probe.c`（完整源码见本章末「附录：工程完整源码」），刻意留了一个有初值的全局、一个字符数组、一个 const 表、一个零初值全局、一个未初始化数组 | 五个对象刚好占满 ELF 的四种归宿，`FileSiz ≠ MemSiz` 那一行必须靠它才出现 |

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 第一刀 ELF 头 | 魔数/类别/机器/入口/程序头计数；Thumb 位初现 | 代码分析 |
| 第二刀 节表 | `Addr`/`Off`/`Size`/`Flg` 四列怎么读；`PROGBITS` 与 `NOBITS` 的分界 | 配置 |
| 第三刀 程序头 | `PT_LOAD` 与 section→segment 映射；VMA/LMA、`FileSiz`/`MemSiz` 实读 | 配置 |
| 全景动画 两副目录 | 文件字节带居中，节表在上、程序头在下，四阶段连线的；`objcopy` 那一刀切掉了什么 | 代码分析 |
| 第四刀 符号表 | `nm -n` 地址流水账；91 个弱别名；`readelf -s` 与 `nm` 的 ±1 | 代码分析 |
| 第五刀 反汇编 | `main` 的 prologue、字面量池、`Reset_Handler` 的搬运循环、数据混进代码区 | 代码分析 |

---

## 第一刀：ELF 头——五个字段就够

```bash
sh probe.sh head
```

```
  Magic:   7f 45 4c 46 01 01 01 00 00 00 00 00 00 00 00 00
  Class:                             ELF32
  Type:                              EXEC (Executable file)
  Machine:                           ARM
  Entry point address:               0x8000189
  Number of program headers:         2
  Number of section headers:         20
```

五件事一次说完：

- **`7f 45 4c 46`** = `0x7F` + `'E' 'L' 'F'`。前四字节就是签名，`file blink.elf` 认的就是它。第五字节 `01` = ELF32（Cortex-M 是 32 位，**不会是 ELF64**），第六字节 `01` = 小端。
- **`Type: EXEC`**：可执行文件，不是共享对象、不是 PIE。裸机没有动态链接器，也没有 ASLR，地址从链接那一刻就焊死了。这正是你能在链接脚本里写死 `0x08000000` 的前提（[B3](03-linker-script.md)）。
- **`Machine: ARM`** + 头里的 `Flags: 0x5000400, Version5 EABI, hard-float ABI`：这一行是"我用的是硬浮点 ABI"的**唯一官方声明**。编译选项和库的 ABI 对不上时，症状是链接通过、跑起来浮点全错，第一个该查的就是这里。
- **`Entry point address: 0x8000189`**：CPU 复位后**不**看这个字段（它看向量表，见第五刀），但 GDB 的 `load`+`break *0x8000189` 看它。
- **`Number of program headers: 2 / section headers: 20`**：**两套目录各有几项**。这 2 与 20 不相等这件事，就是本章第二、三刀的全部内容。

顺手把"差 1"钉死：

```
08000000 r g_pfnVectors
08000188 W Reset_Handler
```

`0x08000188 | 1 = 0x08000189`。**最低位是 Thumb 状态位**。ARMv7-M 架构里 Thumb 位必须为 1，否则硬件直接 fault，所以你写中断向量、写函数指针表时那个 `|1` 是必需的，不是洁癖。

## 第二刀：节表——链接器的抽屉

```bash
sh probe.sh sect
```

先看干净的 blink：

```
  [ 1] .isr_vector  PROGBITS  08000000 001000 000188 00   A
  [ 2] .text        PROGBITS  08000188 001188 00010c 00  AX
  [ 3] .data        PROGBITS  20000000 001294 000000 00  WA
  [ 4] .bss         NOBITS    20000000 000000 000000 00  WA
  [ 5] ._user_heap_stack NOBITS 20000000 002000 000600 00   WA
```

再看标本 elf_probe（`.text` 短一点、`.data`/`.bss` 有货）：

```
  [ 1] .isr_vector  PROGBITS  08000000 001000 000188 00   A
  [ 2] .text        PROGBITS  08000188 001188 0000bc 00  AX
  [ 3] .data        PROGBITS  20000000 002000 00000c 00  WA
  [ 4] .bss         NOBITS    2000000c 00200c 000014 00  WA
  [ 5] ._user_heap_stack NOBITS 20000020 002020 000600 00   WA
```

读表时分别问：运行时放哪、在文件里放哪、占多少字节，以及是什么类型、带什么标志。逐项对照下面的列名：

- **`Addr`（VMA，运行地址）**：先用这一列判断这个节运行时位于哪块存储器。`0x08000000` 属于 Flash，`0x20000000` 属于 RAM。blink 的 `.data`/`.bss`/`._user_heap_stack` 都写着 `0x20000000`，并不是三块内容挤在一起：前两个大小为 0，所以堆栈段直接从 RAM 起始位置开始。
- **`Off`（文件偏移，货架号）**：这个节在 `.elf` 文件里的第几字节。`.text` 的 `Addr=0x08000188` 而 `Off=0x001188`，**差 `0x1000`**。别把两者当一个：换算关系是"减掉 Flash 基址、加上文件里那段表头垫片"。第一个节要到文件第 `0x1000`（4096）字节才开始，前面 4096 字节里只装了 52 字节的 ELF 头和 64 字节的程序头，剩下全是对齐垫子。
- **`Size`**：这一列以字节为单位记录大小。`0x188` = 392，也就是 **98 个 4 字节表项**。可以到 `startup_stm32f407xx.s` 中对照 `g_pfnVectors`：共 98 条 `.word`，分别存放栈顶、复位入口，以及其余异常与中断入口。
- **`Type` + `Flg`**：**`PROGBITS` = 文件里有货，`NOBITS` = 只登记不给货**。`.bss` 是 `NOBITS`：它的 `Off` 甚至是 `000000`，文件里根本没有它的位置，只有一张"请清零"的便条（[C1](../c/01-memory-model.md) 的第一课）。`Flg` 里的 `A`（alloc）是本章最重要的一列：**没有 A 的节，烧录时与你无关**。

blink.elf 有 20 个节，带 `A` 的只有这 5 个。剩下 14 个是给人看的说明书：`.symtab`、`.strtab`、`.shstrtab`、`.comment`、`.ARM.attributes`，以及 **9 个 `.debug_*`**。而 5 个 alloc 节里，`.data` 大小 0、`.bss` 与 `._user_heap_stack` 是 `NOBITS`，**真正在文件里占字节的只有 `.isr_vector` 与 `.text` 两个**。

所以：392 + 268 = **660 字节**，正好是 `size` 的 `text` 列，也正好是 bin 的体积：

```
   text   data   bss   dec   hex   filename
    660      0  1536  2196   894   build/blink.elf
```

```bash
sh probe.sh sect | tail -3     # 顺手看 bin
# bin 只装 ALLOC 段里有货的部分：blink.bin 660 字节
```

**34,604 − 660 = 33,944 字节全是调试信息与符号表**。`objcopy -O binary` 一刀把它们全扔掉，这也是为什么"烧 bin 才谈第几字节"（见常见坑）。

一个易踩的小坑：`size -A` 的地址列是**十进制**。你会看到 `134218120` 这种数，它就是 `0x08000188`；`536870912` 是 `0x20000000`。别以为是编译出问题了。

## 第三刀：程序头——装载器的装车清单

```bash
sh probe.sh seg
```

blink.elf：

```
  Type   Offset    VirtAddr    PhysAddr    FileSiz  MemSiz  Flg Align
  LOAD   0x001000  0x08000000  0x08000000  0x00294  0x00294 R E 0x1000
  LOAD   0x001000  0x20000000  0x08000294  0x00000  0x00600 RW  0x1000

  Segment Sections...
   00     .isr_vector .text
   01     .bss ._user_heap_stack
```

elf_probe.elf（重头戏在第二行）：

```
  LOAD   0x001000  0x08000000  0x08000000  0x00244  0x00244 R E 0x1000
  LOAD   0x002000  0x20000000  0x08000244  0x0000c  0x00020 RW  0x1000
  LOAD   0x000020  0x20000020  0x08000250  0x00000  0x00600 RW  0x1000

  Segment Sections...
   00     .isr_vector .text
   01     .data .bss
   02     ._user_heap_stack
```

这张表才是"装车清单"：

- **一个 `LOAD` = 一批要一起安排到某个地址的东西**。第一个 LOAD 把 `.isr_vector`+`.text` 装进 `0x08000000`，`FileSiz == MemSiz == 0x244`：Flash 里的货有多少，内存里就摆多少，一比一。
- **第二个 LOAD 是全章最精彩的一行**：`VirtAddr=0x20000000`（住址在 RAM），`PhysAddr=0x08000244`（行李在 Flash 的 `.text` 尾巴后面）。**`FileSiz=0x0c` 而 `MemSiz=0x20`**：文件里给 12 字节，RAM 里要 32 字节，差的 20 字节是 `.bss`（`0x14`），文件里不给货，装载者（这里就是启动代码）负责清零。**"有初值才占 Flash，为 0 只占 RAM"这条规则，在 ELF 里就是这两个数的差。**
- **第三个 LOAD `FileSiz=0`**：堆栈预留区，纯粹"分房不带行李"。它的 `Offset=0x000020` 是个提示值，别当真：`FileSiz` 为 0 时文件偏移没有意义。
- **`Flg`：`R E` = 只读可执行（代码），`RW` = 可写（数据）**。想验证有没有把常量错放进可写区，看这里最快。
- **section→segment 映射**：`.data` 与 `.bss` 被并进**同一个** LOAD，因为它们共享一次搬运（搬完 `.data` 顺手清 `.bss`），这正好解释了 `Reset_Handler` 里为什么是两个紧挨着的循环（第五刀见）。

对回源码，链接脚本就那几行（`stm32f407xx.ld`）：

```
 91:  _sidata = LOADADDR(.data);
 95:  _sdata  = .;
 99:  _edata  = .;
100:  } >RAM AT> FLASH
```

`>RAM` 给 VMA，`AT> FLASH` 给 LMA。`_sidata` 于是等于 `0x08000244`：**程序头里的 `PhysAddr` 和符号 `_sidata` 是同一个数的两种写法**，本章实测两者一致。

顺手把 `objdump -s` 与 `readelf -x` 也叫出来，看看 Flash 里那 12 字节的行李长什么样：

```
Contents of section .data:
 20000000 c5ab3412 68656c6c 6f000000           ..4.hello...
```

`c5ab3412` 是 `0x1234ABC5`（`int g_init`，小端倒着写），`68656c6c 6f00` 是 `"hello\0"`，末尾两个 `00` 是补齐对齐。**左边这列地址是 VMA（`0x20000000`），不是它在文件里的位置**。想找那份镜像，得回程序头读 `PhysAddr`。工具默认给你住址，这是新手最容易上当的一处。

## 全景动画：同一份文件，两副目录

第二刀与第三刀读的是同一个 `elf_probe.elf`：中间那条带子是文件里真实的字节顺序，上面挂节表、下面挂程序头。动画四个阶段依次演示：**两套目录各自连到文件的哪一块**、**节表怎么读**（`Addr` 与 `Off` 差 `0x1000`、`NOBITS` 只登记不给货）、**程序头怎么读**（第二条 LOAD 的 `FileSiz=0x0c` 与 `MemSiz=0x20` 之差正是 `.bss`）、**`objcopy` 那一刀切掉了什么**（换 `blink.elf` 看：20 个节只有 5 个带 `A`，进芯片的只有 660 字节）。

![ELF 的两副目录动画](/anim/elf-two-views.svg)

## 第四刀：符号表——nm 一排序就是地图

```bash
sh probe.sh sym
```

`nm -n --print-size build/elf_probe.elf`（省掉 91 行中断别名）：

```
08000000 00000188 r g_pfnVectors
08000188 00000012 t sink
0800019c 0000003c T main
080001d8 00000042 W Reset_Handler
08000238 00000002 t Default_Handler
0800023c 00000008 T tag
08000244 00000000 T _etext
08000244 00000000 A _sidata
20000000 00000004 D _sdata
20000000 00000004 D g_init
20000004 00000006 D g_msg
2000000c 00000004 B _sbss
2000000c 00000004 B g_zero
20000010 00000010 B buf
20000020 00000004 B _ebss
20020000     00000000 R _estack
```

按地址一排序，固件立刻变成地图：

- **`0x08000000 → 0x08000244` 是 Flash**：向量表 392 字节、`sink`/`main`/`Reset_Handler` 依次排开、`tag`（`const` 表）被链接脚本并进了 `.text`，最后 `_etext`/`_sidata` 落在同一个地址 `0x08000244`：**代码的终点就是数据镜像的起点**，一个字节都没浪费。
- **`0x20000000 → 0x20000020` 是 RAM 的已命名部分**：`_sdata`/`g_init`/`g_msg`，紧接着 `_sbss`/`g_zero`/`buf`/`_ebss`。`_edata` 与 `_sbss` 相等（[C1](../c/01-memory-model.md) 里那对"接力棒"符号），搬运与清零的边界就交接在这里。
- **`0x20020000` 是 `_estack`**：RAM 顶，栈从这里往下长。它与 `_ebss` 之间那一大片空地，就是还没人碰过的自由栈/堆空间。
- **字母的含义比你想的少**：`T/t` 是 text 段（大写全局、小写局部），`D/d` 是 `.data`，`B/b` 是 `.bss`，`R` 是只读，`A` 是绝对值符号（链接脚本里 `=` 出来的那些）。但 `tag` 明明只有读的分量却标成 `T`，因为本工程的 `.rodata` 并进了 `.text`。**字母说的是"在哪个输出段、什么属性"，不是"是代码还是数据"。要看真相，看地址。**

再看弱符号：blink.elf 里有 **91 个** 符号指向同一个地址：

```bash
sh probe.sh sym | grep -A1 弱
# 指向 0x080001e8 的 W 别名：91 个
```

```
080001e8 W ADC_IRQHandler
080001e8 W BusFault_Handler
...
```

它们全是 `.globl xxx_IRQHandler; .set xxx_IRQHandler, Default_Handler` 造出来的**弱别名**，真正住在 `0x080001e8` 的是那条 2 字节的死循环 `Default_Handler`（`b.n .`，就地打转等调试器）。**这就是"你没写 `USART1_IRQHandler`，中断来了程序不会跑飞、只会卡在这里"的机理**（弱符号与覆盖规则回到 [C5 函数指针](../c/05-func-pointer.md)与 [B4 启动文件](04-startup.md)）。

最后把那个 ±1 钉死，两个工具同问一个人：

```
   19: 080001e9     2 FUNC  LOCAL  DEFAULT  2 Default_Handler
   78: 08000189    66 FUNC  WEAK   DEFAULT  2 Reset_Handler
  106: 0800020d   136 FUNC  GLOBAL DEFAULT  2 main
```

`nm` 说 `Reset_Handler` 在 `08000188`、`main` 在 `0800020c`；`readelf -s` 说 `08000189`、`0800020d`。**`readelf` 保留 Thumb 位、`nm` 抹掉它**。所以：往向量表里填函数地址时那位 `|1` 必须有；而在链接脚本/map 文件里看到的地址通常不带。差 1 不是 bug，是两位工具的不同口径。

## 第五刀：反汇编——把固件慢放

```bash
sh probe.sh dis
```

先看 `main` 的三条开头（`blink.elf`，`-O0`）：

```
0800020c <main>:
 800020c:  b580        push {r7, lr}
 800020e:  af00        add  r7, sp, #0
 8000210:  4b19        ldr  r3, [pc, #100]  @ (8000278 <main+0x6c>)
 8000212:  681b        ldr  r3, [r3, #0]
 8000216:  f043 0320   orr.w r3, r3, #32
```

- `push {r7, lr}` + `add r7, sp, #0` 就是 [C6 栈帧](../c/06-abi-stack.md) 讲的 prologue，**源码里看不到，机器码里跑不掉**。
- `orr.w r3, r3, #32` 里的 `#32` 就是源码里的 `1UL << 5`（`RCC_AHB1ENR_GPIOFEN`，bit5）。**十六进制/十进制的转换是编译器干的活**，这也是你日后在 GDB 里认指令的老本行。
- 注意 `ldr r3, [pc, #100]`：**指令里没有 `0x40023830` 这个外设地址**。它躺在 `main` 尾巴后面：

```
 8000278:  40023830   .word 0x40023830
 800027c:  40021400   .word 0x40021400
 ...
 800028c:  40021418   .word 0x40021418
 8000290:  001e8480   .word 0x001e8480
```

这叫**字面量池（literal pool）**：Thumb 的 16 位指令塞不下 32 位常量，编译器就把常量就近放在代码段里，用 `pc` 相对寻址取。`0x40021400/404/408/40c/418` 正是 `GPIOF` 的 `MODER/OTYPER/OSPEEDR/PUPDR/BSRR` 五个寄存器，`0x001e8480` 是 `delay(2000000)` 的那个 2000000（`0x1E8480`）。**它们都在 `.text` 里，占的是 Flash。** 想知道你的常量到底花在哪，`objdump -d` 比 `size` 更诚实。

再看 `Reset_Handler`（`elf_probe.elf`，B4 的主角；本章只点出它和第三节的关系）：

```
080001d8 <Reset_Handler>:
 80001d8:  f8df d040   ldr.w sp, [pc, #64]   @ 800021c   → 0x20020000
 80001dc:  4810        ldr  r0, [pc, #64]    @ 8000220   → 0xe000ed88
 80001e0:  f441 0170   orr.w r1, r1, #15728640  @ 0xf00000
 80001f8:  58d4        ldr  r4, [r2, r3]
 80001fa:  50c4        str  r4, [r0, r3]
 80001fc:  3304        adds r3, #4
 8000214:  f7ff ffc2   bl   800019c <main>
 ...
 800021c:  20020000    .word 0x20020000   @ _estack
 8000220:  e000ed88    .word 0xe000ed88   @ SCB->CPACR
 8000224:  20000000    .word 0x20000000   @ _sdata
 8000228:  2000000c    .word 0x2000000c   @ _edata
 800022c:  08000244    .word 0x08000244   @ _sidata
 8000230:  2000000c    .word 0x2000000c   @ _sbss
 8000234:  20000020    .word 0x20000020   @ _ebss
```

**第三节那两个看起来神秘的地址，最后就是在这里被读进寄存器的**：`0x20000000`（VMA，目的地）、`0x08000244`（LMA，出发地）、`0x2000000c`（`_edata`，终点），`ldr r4,[r2,r3]` / `str r4,[r0,r3]` / `adds r3,#4` 就是一个字一个字往 RAM 里搬。搬完再照着 `_sbss`→`_ebss` 清一遍，然后 `bl main`。顺带看见 `0xe000ed88` = `SCB->CPACR`、`#0xf00000` = CP10/CP11 全权限（`startup_stm32f407xx.s:42`），**硬浮点在 `main` 的第一行代码之前就已经开好了**，这正是 ELF 头里 `hard-float ABI` 敢写死的原因。

最后是本章最"惊悚"的一幕，`objdump -d` 会顺手把数据当代码反汇编：

```
08000238 <ADC_IRQHandler>:
 8000238:  e7fe   b.n  8000238 <ADC_IRQHandler>
0800023c <tag>:
 800023c:  434d 0055 0000 0000    MCU.....
```

`tag` 是 `const uint8_t tag[8] = {'M','C','U',0,...}`，**它就住在 `.text` 里**。反汇编器照着 Thumb 的两字节规则切成 `434d 0055`，你看到的是"MCU....."，这不是乱码，是**你把数据读成了指令**。以后在 `objdump -d` 里看见成片的 `.short 0x0000` / "undefined instruction"，先怀疑那是字面量池或常量表，而不是编译器坏了（回 [C1](../c/01-memory-model.md) 的 `.rodata` 并入 `.text` 那一节）。

## 实物实验：一个 8 字节数组，加不加 const

```bash
cd code/toolchain/02-elf
sh probe.sh tag
```

同一份 `elf_probe.c`，只把 `tag` 前面的 `const` 拿掉（`-DTAG_RAM`）：

| 实测项 | `const uint8_t tag[8]` | `uint8_t tag[8]` |
|---|---|---|
| `nm` 里的 `tag` | `0800023c 00000008 T tag` | `2000000c 00000008 D tag` |
| `.text` | 188 | **180**（少 8） |
| `.data` | 12 | **20**（多 8） |
| `.bss` | 20 | 20 |
| 第二个 LOAD | `VirtAddr=0x20000000 PhysAddr=0x08000244 FileSiz=0x0000c MemSiz=0x00020` | `VirtAddr=0x20000000 PhysAddr=0x0800023c FileSiz=0x00014 MemSiz=0x00028` |

读这张表：加 `const` 之后，`tag` 从 `D` 变 `T`、住址从 RAM 的 `0x2000000c` 搬到 Flash 的 `0x0800023c`；`.data` 从 20 缩回 12、`.text` 从 180 涨到 188。程序头第二行的 `FileSiz` 也从 `0x14`(20) 回到 `0x0c`(12)、`MemSiz` 从 `0x28`(40) 回到 `0x20`(32)。

**净效果：省掉 8 字节 RAM（那 8 字节的本体不再需要在 RAM 里存在），Flash 总量一格没变。** 一个 `const` 字，买的是"别再往 RAM 搬一遍"，这正是 [C1](../c/01-memory-model.md) 用 256 字节表算过的那笔账，在 ELF 结构层面的样子。

## 附录：工程完整源码

五刀切的那具标本本体（正文所有地址、大小、字母都出自它和 `../../stm32/00-blink`）：

<<< ../../code/toolchain/02-elf/elf_probe.c

一条命令跑完五刀（正文每条命令的包装、`-DTAG_RAM` 对照也在这里）：

<<< ../../code/toolchain/02-elf/probe.sh

## 记忆锚点

::: tip 一句话记住
**头说我是谁，节说我有几抽屉，程序头说怎么装车；`A` 标记之外全是说明书，`FileSiz` 与 `MemSiz` 的差就是启动代码的工作量。**
:::

::: warning 那个 1
`readelf` 给你 `0x8000189`，`nm` 给你 `0x08000188`。**差 1 的是 Thumb 位**：往向量表和函数指针里填地址时必须带 1，工具之间对照时必须先抹平。
:::

## 常见坑

- **把文件偏移当内存地址**：`.text` 的 `Addr=0x08000188`、`Off=0x001188`。谈"烧到第几字节"要用 bin 的偏移（`.text` 在 bin 里就是第 392 字节起），谈"程序跳到哪"要用 VMA。两套口径混用，就会把断点打在数据上。
- **拿 `.elf` 的体积估固件体积**：`blink.elf` 34,604 字节 vs 烧进去 660 字节。**看 `size` 的 `text`+`data` 估 Flash、`data`+`bss` 估 RAM**（blink：Flash 660，RAM 0+1536）；`dec` 是两者相加，别当成 Flash 占用。B5 会把这笔账算到 map 文件级别（[B5 体积从 map 倒推](05-map-size.md)）。
- **只盯 `.text` 就下结论**：`.rodata` 在本工程被并进 `.text`（`stm32f407xx.ld:48-49`），常量、字符串、跳表都藏在里面。`objdump -d` 看到 `.word` 成串才是真相（[C1](../c/01-memory-model.md) 的 `.rodata` 单列实验会告诉你字母为什么会变）。
- **"反汇编出现 undefined instruction"**：多半是数据被当代码（本章的 `MCU.....` 就是现场）。要读原始字节，用 `objdump -s -j .text` 或 `readelf -x`，别用 `-d`。
- **符号找不到就先怀疑编译档**：函数里的 `int auto_var` 在符号表里查无此人，它活在栈上，链接期根本不存在（[C1](../c/01-memory-model.md) 已实测）。同理，`static` 局部变量有符号、`auto` 局部变量没有。

## 短自测

1. `blink.elf` 有 34,604 字节，烧进芯片只有 660 字节。差额是什么？为什么 `size` 命令的 `text`+`data` 才是 Flash 占用？
<details><summary>参考答案</summary>差额是调试信息（`.debug_*` 段）和符号表，它们写给活人看，不进芯片。`size` 的 `text` 含 `.text`+`.rodata`（代码与常量），`data` 含 `.data`（有初值全局变量），两者之和才是真正占 Flash 的字节；`bss` 只占 RAM 不占 Flash。</details>

2. `.data` 的 `VirtAddr=0x20000000`、`PhysAddr=0x08000244`。启动代码在进 `main` 之前必须做什么？搬多少字节？
<details><summary>参考答案</summary>启动代码必须把 `.data` 的初值从 Flash（LMA=0x08000244）拷贝到 RAM（VMA=0x20000000），搬运字节数 = `FileSiz`（不是 `MemSiz`：`MemSiz` − `FileSiz` 的部分是 `.bss`，用 memset 清零而非拷贝）。这段逻辑在启动文件的 `LoopCopyDataInitDone` 标签处。</details>

3. `readelf -h` 显示入口 `0x8000189`，`nm` 显示 `Reset_Handler` 在 `0x08000188`。差 1 是谁错了？在 GDB 里设断点该用哪个地址？
<details><summary>参考答案</summary>都没错。Cortex-M 只跑 Thumb 态，函数地址的最低位（bit 0）是 Thumb 状态标志位，不是地址位。ELF 入口地址保留了这一位（`0x...9` = `0x...8 | 1`），告诉 CPU "跳过去之后用 Thumb 指令集"。`nm` 显示的是纯地址 `0x...8`。在 GDB 里设断点用 `break *0x08000188`（纯地址），但往向量表或函数指针里填值时必须带 1。</details>

## 延伸阅读

两副目录的原始定义与两本教科书：

- **[\[C3\]](../reference/bibliography.md#toolchain)** TIS ELF 1.2 — 节头表/程序头表的原始规范，二十来页讲完。
- **[\[E2\]](../reference/bibliography.md#books)** Levine《Linkers and Loaders》第 3 章 · **[\[E3\]](../reference/bibliography.md#books)** 《程序员的自我修养》第 3 章 — ELF 结构的教科书式讲法，中英各一本。

## 你做到了

- 五刀拆完一具真固件：ELF 头 → 节表 → 程序头 → 符号表 → 反汇编；
- 能读出 `FileSiz`/`MemSiz` 之差背后的启动工作量，并认出那对 VMA/LMA 是从链接脚本哪一行来的；
- 见过 Thumb 位、字面量池、91 个弱别名，以及"数据被反汇编成指令"的现场。

开场那笔「烧进去的只有几百字节、文件却有几十 KB」的差额账，你现在能逐项报出明细：哪些是写给链接器的目录，哪些是给装载器的，哪些根本不进芯片。那份「写给活人看的说明书」从此是你能查的档案，不是玄学。

<div class="achievement">
✅ 下一站：<a href="03-linker-script.html">B3 链接脚本</a>。本章读了 <code>_sidata = LOADADDR(.data)</code> 与 <code>AT&gt; FLASH</code> 兑现出来的地址；下一站逐行讲图纸是怎么规定这些地址的，包括那个把 <code>.rodata</code> 并进 <code>.text</code> 的决定。
</div>

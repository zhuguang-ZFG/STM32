---
title: B3 链接脚本：固件的建筑图纸
status: done
difficulty: 3
minutes: 45
---

# B3 链接脚本：固件的建筑图纸

> 🎯 删掉一个词（`AT> FLASH` 里的 `AT>`），固件照样链接成功，烧进去照样跑，只是每个初值都成了随机数。图纸的力量不在语法，在契约。

本章全部数字出自同一套工具链的实测：xPack GNU Arm Embedded GCC **15.2.1 (20251203)**，binutils **2.45.1**。图纸是 `code/stm32/00-blink/stm32f407xx.ld`（136 行），六刀由 `code/toolchain/03-linker/probe.sh` 现场切，每刀只用 `sed` 改一行，diff 打在输出里，原文不动，你在自己机器上复跑得到同一串字节。

## 本章精髓

1. **图纸产出的不是代码，是三份地址契约**：`MEMORY` 圈地（哪块地能住人）、`SECTIONS` 分房（谁住哪间、谁住头排）、符号门牌（`_estack`/`_sidata`/`_sdata`……）留给启动代码兑现。契约写错，链接器多半不报错，它只按你说的做，做得很彻底。
2. **一个段有两个住址**：VMA（运行时在哪）与 LMA（初值存在哪）。`>RAM AT> FLASH` 这一句在 ELF 里兑换成第二条 LOAD；`objcopy -O binary` 只认 LMA，所以少写一个词，bin 能从 660 字节变成 **134,217,744 字节**。
3. **图纸能在链接期就拦下运行期事故**：`._user_heap_stack` 那一间一个真实字节都不占，它只是向 RAM 借的额度。`region 'RAM' overflowed by 4616 bytes` 出现在构建窗口里，好过出现在客户手里。

- **能理解**：六刀各改一个词，输出为什么长成那样，每段下面都贴了实测文本，可以逐字核。
- **能用**：给自己的变量加一间自定义段（本章用 F407 的 64KB CCM），并知道加完还必须补哪一段启动代码，否则初值到不了。

## 先修

- [B2 ELF 解剖](02-elf.md)（节表 / 程序头 / VMA 与 LMA 的分家，本章负责讲清"是谁规定它们的"）
- [C1 内存模型](../c/01-memory-model.md)（一个全局变量的三段旅程）
- [B4 启动过程](04-startup.md)（本章的门牌由谁来读。顺序反了也不影响，两边互相引用）

## 先跑起来（10 分钟 quick win，**不用开发板**）

先别急着跑：这一刀要删掉链接脚本里的 KEEP。押两问：删完链接器会不会报错？固件变大还是变小？押完再看两份尺寸。

```bash
sh code/toolchain/03-linker/probe.sh keep
```

盯住输出里这两行：

```
blink.bin  = 660 字节
nokeep.bin = 268 字节
差 = 392 字节 = 0x188
```

只把 `KEEP(` 这个字母序列删掉，向量表那 392 个字节就从固件里蒸发了，而且 `readelf -S` 还给你留一个尺寸 0 的段名当遗照。这一刀是本章最短的一条命令、最长的一节课。

## 图纸全貌：136 行，三段结构

三份契约先看图：MEMORY 圈地、SECTIONS 分房、符号留门牌——.data 的双住址是全图的主角。

![链接脚本三契约：FLASH 与 RAM 两块圈地，.data 的双住址连线](/arch/linker-map.png)

```
stm32f407xx.ld
├── 契约头      :13-20   ENTRY / _estack / 两份最小预算
├── MEMORY 圈地 :22-29   FLASH 1MB @0x0800_0000、RAM 128KB @0x2000_0000
└── SECTIONS 分房 :31-136  .isr_vector → .text → .data → .bss → ._user_heap_stack → 收尾
```

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| MEMORY 地块 | F407 的三块地（FLASH/RAM/CCM）；属性字母只有 `r w x a i l`；map 的 `Memory Configuration` 回显 | 配置 |
| 向量表落位 | 头排 + `KEEP` 的分工：一个管地址，一个管生死 | 配置 |
| .data 的双地址 | `>RAM AT> FLASH` 逐词讲；map 里 `load address` 那一行；程序头三条 LOAD | 配置 |
| 符号界碑 | `_estack/_sidata/_sdata/_edata/_sbss/_ebss` 六个门牌在反汇编字面量池里的真身 | 代码分析 |
| 自定义段实战 | `.ccmram` 三态：orphan 撒谎 / 128MB 空洞 / `AT>` 收场 / 启动文件不搬 | 代码分析 |
| 栈堆预算 | `._user_heap_stack` 检查段与 `overflowed by N bytes` | 配置 |
| 取证六刀 | 每刀的 `sed` diff + 原文报错，全部 `probe.sh` 可复跑 | 代码分析 |

## 逐行读：契约头与 MEMORY

```ld
ENTRY(Reset_Handler)                        /* :13 */
_estack = ORIGIN(RAM) + LENGTH(RAM);        /* :16 */
_Min_Heap_Size  = 0x200;                    /* :19 */
_Min_Stack_Size = 0x400;                    /* :20 */
```

- `ENTRY(Reset_Handler)` 只对**链接器**说话：它决定 ELF 头里的 `Entry point address`，也决定 `-u`/`--gc-sections` 的根集合之一。而**芯片不看这一行**：上电后硬件从 `0x08000000` 连读两个字：第一个当初始 SP，第二个当复位 PC（[B2 第五刀](02-elf.md) 拆过那条向量表，[B4](04-startup.md) 讲它的来源）。你把 bin 烧进芯片，ELF 头连字节都不剩。所以"入口"有两套口径：`readelf -h` 的那个是给装载器看的，向量表第 2 项才是给 silicon 的。
- `_estack = ORIGIN(RAM) + LENGTH(RAM)` 算出来是 `0x20000000 + 0x20000 = 0x20020000`，实测 `nm` 给 `20020000 R _estack`，`blink.bin` 的头一个字正是它（第 1 刀会看到它被顶掉）。注意这是**栈顶**，栈向下生长，从 RAM 最后一字节的上一格开始。
- 两份 `_Min_*` 不是分配，是**额度**：稍后 `._user_heap_stack` 用 `. = . + _Min_Stack_Size;` 把它记在 RAM 的账上（`:122-123`）。

```ld
MEMORY
{
  FLASH (rxa)  : ORIGIN = 0x08000000, LENGTH = 1024K   /* :24 */
  RAM   (xrw)  : ORIGIN = 0x20000000, LENGTH = 128K    /* :28 */
}
```

- `ORIGIN`/`LENGTH` 两个数错一个，链接出来的就是"盖在别人家的房子"。F407ZGT6 的事实：Flash 1MB 从 `0x0800_0000`（RM0090 存储器映射表，S1 已核过）、SRAM 128KB 从 `0x2000_0000`。
- 括号里是**区域属性**。合法字母只有 `r w x a i l` 六个。老教程（包括 ST 早年的模板）常写 `(xrwah)`，多一个 `h`。旧 binutils 睁只眼闭只眼，2.45.1 直接拒绝：

```
invalid character %c (104) in flags
error: ld returned 1 exit status
```

  `104` 就是字母 `h` 的 ASCII 码。那句 `%c` 不是我们抄漏了字，是 binutils 自己的格式串没带参数。**报错原文照抄才有价值**，遇到它别去找"字符 104 是什么"，直接把 `h` 删掉。
- 图纸写完，链接器会在 map 文件里回显它理解的地块：

```
Memory Configuration

Name             Origin             Length             Attributes
FLASH            0x08000000         0x00100000         axr
RAM              0x20000000         0x00020000         xrw
*default*        0x00000000         0xffffffff
```

  属性被按固定顺序重排成 `axr`（你写的是 `rxa`），这是**图纸生效的第一处证据**。`*default*` 那行是"没进任何地块的东西"的去向，第 5 刀会用到它。

## SECTIONS 第一间：向量表必须住头排

```ld
  .isr_vector :
  {
    . = ALIGN(4);
    KEEP(*(.isr_vector))     /* :38 */
    . = ALIGN(4);
  } >FLASH
```

- **`.` 是"当前地址"，不是"当前偏移"**：在没有 `AT>` 的输出段里，`.` 就是 VMA。`. = ALIGN(4)` 把它抬到 4 字节边界，Cortex-M 的向量表项必须是字对齐的 32 位地址。
- **`*` 的两层含义**：`*(.isr_vector)` 读作"所有输入文件里名叫 `.isr_vector` 的段"。输入段名来自启动文件的汇编（`startup_stm32f407xx.s` 里 `.section .isr_vector,"a",%progbits`），图纸与启动文件是**一套榫卯**：一个声明名字，一个认领名字。
- **`KEEP()` 管生死**：本工程链接带 `-Wl,--gc-sections`（B2 见过它砍掉 33,944 字节里的哪几刀），GC 的判据是"有没有人引用"。向量表没有被任何代码引用，是**硬件**读它，而硬件不出现在符号表里。`KEEP()` 就是给链接器塞的小抄：这个段不许回收。

### 第 1 刀：把 KEEP 去掉

```
38c38
<     KEEP(*(.isr_vector))
---
>     *(.isr_vector)
```

后果按三层看：

```
blink.bin  = 660 字节
nokeep.bin = 268 字节
差 = 392 字节 = 0x188
```

```
  [ 1] .isr_vector  PROGBITS  08000000 001000 000188 00  A  0  0  1     ← 正常
  [ 1] .isr_vector  PROGBITS  08000000 00110c 000000 00  W  0  0  1     ← 空壳
```

段名、段号都还在，**尺寸变成 0**，`readelf -S` 不会告诉你出事了。第三层最要命：硬件上电从 `0x08000000` 读的那两个字。

```
blink.bin  头两个字:  20020000 08000189
nokeep.bin 头两个字:  d040f8df 68014810
```

正常版本第一个字是 `_estack`、第二个是 `Reset_Handler | 1`（Thumb 位，B2 那个"差 1"的坑）。被砍掉向量表之后，`.text` 顶到 `0x08000000`，于是芯片把**两条指令的机器码**当成 SP 和 PC 用：`SP = 0xd040f8df`，第一条压栈指令就打死机。`nm` 里 `08000000 r g_pfnVectors` 这个符号也一并消失，**它是你排查"板子毫无反应"时最该先看的一行**。

## `.data` 的双地址：一句 `>RAM AT> FLASH`

先把"人在 RAM、货在 Flash"画出来：两个住址、一个搬运工、一个删词即翻车的反例。

![.data 的 VMA 与 LMA 动画](/anim/data-vma-lma.svg)

```ld
  _sidata = LOADADDR(.data);                 /* :91 —— 门牌在段之前就发 */
  .data :
  {
    . = ALIGN(4);
    _sdata = .;                              /* :95 */
    *(.data)
    *(.data*)
    . = ALIGN(4);
    _edata = .;                              /* :99 */
  } >RAM AT> FLASH                           /* :100 */
```

逐词读：`>RAM` 说**运行时住在 RAM**（VMA），`AT> FLASH` 说**初值行李寄存在 Flash**（LMA）。中间没有别的语法糖，两个住址就靠这一句绑起来。`LOADADDR(.data)` 取的是后一个（LMA），所以 `_sidata` 是"去 Flash 哪里取货"。

实测两副样子。带 `AT> FLASH` 的基线，程序头三条：

```
  LOAD  0x001000  0x08000000  0x08000000  0x00218  0x00218 R E
  LOAD  0x002000  0x20000000  0x08000218  0x00004  0x01008 RW
  LOAD  0x000008  0x20001008  0x0800021c  0x00000  0x00600 RW
```

第二行 `VirtAddr=0x20000000 / PhysAddr=0x08000218 / FileSiz=4 / MemSiz=0x1008`：`FileSiz` 只有 4 字节（标本里 `g_live` 一个 int），`MemSiz` 是 4104：这就是 B2 说的"差值是启动代码的工作量"，本页补上"差额从哪来"。`nm` 给 `08000218 A _sidata`。map 文件里那一行更是直说：

```
.data   0x20000000   0x4  load address 0x08000218
```

### 第 2 刀：删掉 `AT> FLASH`

```
100c100
<   } >RAM AT> FLASH
---
>   } >RAM
```

```
  LOAD  0x001000  0x08000000  0x08000000  0x00218  0x00218 R E
  LOAD  0x002000  0x20000000  0x20000000  0x00004  0x01608 RW
```

三条 LOAD 塌成两条，`.data` 的 `PhysAddr` 变成 `0x20000000`，和 `VirtAddr` 一模一样。符号表随之变成：

```
20000000 D _sdata
20000004 D _edata
20000000 A _sidata        ← 本来是 0x08000218
```

启动文件那个循环（`ldr r0,=_sdata / ldr r1,=_edata / ldr r2,=_sidata`，B4 逐条讲过）于是"把 `_sdata` 拷到 `_sdata`"，一个字节也没搬。而 Flash 里那 4 个初值字节仍在，**它们只是没人来取的快递**。上电瞬间 RAM 是随机值，`g_live` 读到多少全看运气和温度。

这个 bug 的恶心之处：链接不报错、烧录不报错、`readelf -h` 漂亮、多数时候程序"看起来在跑"（RAM 恰好残留了上次的值）。**判据只有一条：`nm` 里 `_sidata != _sdata`。**

## 符号界碑：六个门牌在机器码里的真身

`_estack/_sidata/_sdata/_edata/_sbss/_ebss` 不是给 C 用的，是给启动文件用的。链接完成后它们会被"物化"进 `Reset_Handler` 的字面量池。实测（`objdump -d build/base.elf`，标本为 `link_probe.c`）：

```
 80001cc:  .word 0x20020000    ← _estack（第一条 ldr.w sp,[pc,#64] 直接写进 SP）
 80001d0:  .word 0xe000ed88    ← SCB->CPACR，使能 FPU（B4 的第 0 步）
 80001d4:  .word 0x20000000    ← _sdata
 80001d8:  .word 0x20000004    ← _edata
 80001dc:  .word 0x08000218    ← _sidata
 80001e0:  .word 0x20000004    ← _sbss
 80001e4:  .word 0x20001008    ← _ebss
```

对着 `nm` 看，一个不差。三个细节值得留意：

- `_sbss == _edata == 0x20000004`：`.bss` 紧贴在 `.data` 后面，所以清零循环的起点是"搬运循环的终点"，两个循环共用一个指针推进方式（`str.w r3,[r2],#4` 那条自增存）。
- `_ebss = 0x20001008 = _sbss + 0x1004`，`0x1004 = 4100` 就是 `g_dark` + `g_big[4096]`。
- 这些是**链接期算出来的常量**，不是运行期查询。改图纸、加数组，池子里的字面量跟着变，所以启动文件不需要"知道"你有几个全局变量。

## 第 3 刀：图纸在链接期拦住你

先量一次账（`link_probe.c` 的标本，原图纸）：

```
Memory region         Used Size  Region Size  %age Used
           FLASH:         540 B         1 MB      0.05%
             RAM:        5640 B       128 KB      4.30%
```

**5640 是能手算的**：`.data` 4 + `.bss` (4 + 4096) + `._user_heap_stack` (0x200 + 0x400 = 1536) = 5640。把这一格记住，下面两个报错就能自己验算。

3a：`sed 's/LENGTH = 128K/LENGTH = 2K/'`，只改地块大小，C 代码一个字没动：

```
build/tinyram.elf section `.bss' will not fit in region `RAM'
region `RAM' overflowed by 3592 bytes
error: ld returned 1 exit status
```

`5640 − 2048 = 3592`，与 ld 报的数一字不差。ld 先点名段（`.bss`），再说总量：**先看点名，就知道该减谁的量**。

3b：把数据全删干净，只把栈预算从 `0x400` 撑到 `0x20000`：

```
build/bigstack.elf section `._user_heap_stack' will not fit in region `RAM'
region `RAM' overflowed by 4616 bytes
             RAM:      135688 B       128 KB    103.52%
```

点名的 `._user_heap_stack` 里**一个真实字节都没有**，纯粹是 `. = . + _Min_Stack_Size;`（`:122-123`）立起来的界碑。它换来的是：栈不够用这件事，在构建窗口里以 `103.52%` 的形式失败，而不是在客户手上以踩内存的形式失败。`135688 − 131072 = 4616`，同样能手算。

## 第 5 刀：CCM 的三态（本章最值钱的一刀）

F407 有第三块地：64KB CCM RAM @ `0x1000_0000`（S1 的总线矩阵动画里那个"DMA 够不着、只有 CPU 能到"的房间）。标本 `link_probe.c` 加 `-DWITH_CCM` 会多一个成员：

```c
__attribute__((section(".ccmram"), used)) int g_ccm[4] = { 1, 2, 3, 4 };
```

### 态一：只改 C，图纸没留房间

用原图纸链接，`objdump -h` 的第三行：

```
  3 .ccmram  00000010  20000004  08000230  00002004  2**2
```

VMA 是 `0x2000_0004`：**它就在普通 SRAM 的第 5 个字节**，跟 CCM 毫无关系。ld 一声不响（orphan 段被按 `*default*` 的规矩随手安置了）。你在 C 里写 `g_ccm`，编译器满意，链接器满意，只有你对"它在 CCM"这件事是误解。这一态的杀伤力在于：**测不出来**，它明明能用，只是不在你以为的地方（于是 DMA 能不能访问、速度多少，全都与预期不符）。

### 态二：图纸加了房间，但只写 `>CCM`

```ld
  CCM   (rw)   : ORIGIN = 0x10000000, LENGTH = 64K
  ...
  .ccmram : { _siccm = .; _sccm = .; KEEP(*(.ccmram)) _eccm = .; } >CCM
```

程序头多出第四条：

```
  LOAD  0x003000  0x10000000  0x10000000  0x00010  0x00010 RW
```

`VirtAddr = PhysAddr = 0x10000000`：没有 `AT>`，LMA 就跟着 VMA 走。现在 `objcopy -O binary` 面对的是"要把货物放在 0x1000_0000，而镜像从 0x0800_0000 开始"，它老实照办、一声不响地补零：

```
objcopy  exit=0
bin 尺寸 = 134217744 字节
```

`0x10000000 − 0x08000000 = 134,217,728`，再加 16 字节初值 = **134,217,744**。660 字节的固件写"占用了 Flash 1 MB 的 0.05%"，改一个词的图纸让 bin 膨胀到 128MB，而烧录器会忠实地把这 128MB 往 Flash 里灌。

### 态三：补上 `AT> FLASH`

同一个位置，`>CCM AT> FLASH`：

```
  LOAD  0x002000  0x10000000  0x0800022c  0x00010  0x00010 RW
bin 尺寸 = 576 字节
```

LMA 回到 Flash（`0x0800022c`，紧贴在 `.text` 之后），bin 从 134,217,744 收回 **576 字节**：`0x0800023c + 4 = 0x240 = 576`，一个字节都不多。**`AT>` 就是把"人在 RAM"和"货在 Flash"这两件事分开写的那半句**，CCM 这种"离群的地块"最能看出它的价值。

### 态四：可是初值到得了 CCM 吗？

```
startup 里引用过这些符号的次数：_sidata=3 / _siccm=0
```

`Reset_Handler` 的反汇编里只有一个搬运循环和一段清零循环：

```
 80001a8:  ldr  r4, [r2, r3]     ← 从 _sidata 取
 80001aa:  str  r4, [r0, r3]     ← 写进 _sdata
 80001ac:  adds r3, #4
 80001b0:  cmp  r4, r1           ← 到 _edata 为止
 80001b2:  bcc.n 80001a8
```

`_siccm/_sccm/_eccm` 三块门牌立在图纸上，**启动文件里没有一条指令走过去**。即使 LMA 正确、初值躺在 Flash 里等取，也没人来取；上电后 CCM 里那 16 个字节仍是随机值。想让带初值的变量真住进 CCM，得自己在启动文件补第二段拷贝（照抄 `.data` 那四条指令，把三个符号换成 `_siccm/_sccm/_eccm`）。

**这就是"图纸与启动文件是一套榫卯"的反面教材**：图纸单方面开了房间，施工队不知道。

## 第 6 刀：让链接器自己交代它干了什么

三条开关，出问题的第一步都该按它们来：

- **`-Wl,--print-memory-usage`**：每块地的账（上面那两个表就是它打的）。RAM 从 `4.30%` 变成 `103.52%` 这类跳跃，一眼就知道是栈预算还是大数组。
- **`-Wl,--trace`**：谁被链进来了。实测前几行：

```
build/startup.o
build/main.o
  …thumb/v7e-m+fp/hard\libgcc.a
  …thumb/v7e-m+fp/hard\libc.a
  …thumb/v7e-m+fp/hard\libm.a
```

  `thumb/v7e-m+fp/hard` 这一串目录名就是 **多架构（multilib）选择**：由 `-mcpu=cortex-m4 -mfpu=fpv4-sp-d16 -mfloat-abi=hard` 三个开关共同决定。改成 soft-float 会去另一个目录找库，找不到就报 `cannot find -lgcc`，这明明是装了库的机器上最容易看不懂的一类错，答案在 `--trace` 里一行就能看到。另外 `libc.a` 出现两次不是重复链接：archive 会被反复扫描，直到不再有新的目标文件被拉出来。
- **`ld --verbose`**：不打 `-T` 时它默认用哪张图纸。实测开头：

```
Supported emulations:
 armelf
using internal linker script:
OUTPUT_FORMAT("elf32-littlearm", "elf32-bigarm", "elf32-littlearm")
OUTPUT_ARCH(arm)
ENTRY(_start)
```

  内置图纸的入口是 `_start`、且完全没有 `MEMORY` 块，所以裸用 `ld` 不写 `-T`，程序会被塞进默认的 `TEXT`/`DATA` 布局，跟 0x08000000 没有半点关系。**`-T` 不是可选的美化，是芯片能启动的前提。**

## 记忆锚点

::: tip 一句话记住
**链接脚本不产代码，产三份地址契约：`MEMORY` 圈地、`SECTIONS` 分房、符号留门牌；一个段有两个住址：VMA 管运行、LMA 管初值，少写一个 `AT>`，bin 从 660 字节胀成 134MB。**
:::

**延伸**：.data 的 VMA/LMA 双住址在 [B2 ELF 段视图](02-elf.md) 有动画演示；栈堆的 `_Min_*` 预算段与启动文件配合见 [B4 启动文件](04-startup.md)；Flash 调试时断点与地址关系见 [B6](06-flash-debug.md)。

## 实物实验

::: warning 这一节还没上板
下面三条需要接 F407 + ST-Link，本章只做到"链接期与文件期已核实"。**板上现象一律标待回填**，不许拿 `objdump` 的结论冒充眼睛看到的结论。
:::

| 实验 | 观测点 | 预期（工具链侧已核实） | 板上 |
|---|---|---|---|
| 第 1 刀的固件烧进去 | 串口有无输出、SWD 能否连上 | `SP=0xd040f8df`，第一条压栈即 HardFault/锁死 | 待回填 |
| 第 2 刀烧进去 | `g_live` 打印值 | 每次上电不同（RAM 残留） | 待回填 |
| 第 5 刀态二 | 烧录器进度条 | 灌 128MB，耗时以十秒计，且地址越界报错 | 待回填 |

安全做法：**用第 6 刀的三条开关在构建期判死**，不要靠"烧进去看看"。链接脚本的错，绝大多数在链接期就该被拦下。

## 常见坑

按新手实际撞上的频率排：

1. **忘 `KEEP()`，向量表被 gc**：`--gc-sections` 只认引用关系，不认硬件。指纹是 `readelf -S` 里 `.isr_vector` 尺寸 0（段名还在！）、`nm` 查不到 `g_pfnVectors`、bin 突然小 392 字节。
2. **自定义段没在图纸登记就开用**：orphan 段被静默安置到 `0x20000004`，零警告。判据：`objdump -h` 看那个段的 VMA 是不是你预期的地块地址。
3. **`AT>` 漏写**：`.data` 的 LMA 塌进 RAM，`_sidata == _sdata`，初值永远搬不到位。判据一条：`nm | grep _sidata`，它必须是个 `0x0800xxxx`。
4. **区域属性照抄老教程**：`(xrwah)` → `invalid character %c (104) in flags`。合法字母只有 `r w x a i l`。
5. **改了 `ORIGIN` 忘了改烧录地址**：图纸把代码放 `0x08004000`（bootloader 场景常见），烧录器还在往 `0x08000000` 写，芯片从老地方读栈顶，读到你上一版固件。两侧地址必须一起改。
6. **把 CCM 当普通 RAM**：S8 讲过 DMA 够不着 CCM（总线矩阵只把 CCM 接到 CPU）；本章补上另一半：**图纸没登记 + 启动文件不搬**，所以带初值的 CCM 变量上电是垃圾。DMA 缓冲区放 CCM 是无声失败，初值放 CCM 也是无声失败，两种失败还不一样。
7. **把 `._user_heap_stack` 的报错当成"代码太大"**：它点名的是检查段，问题往往是 `_Min_Stack_Size` 或某个 `.bss` 大数组。先跑 `--print-memory-usage` 看占比。

## 短自测

1. `.data` 的 VMA 和 LMA 分别是什么？谁读 VMA、谁读 LMA？
2. 删掉 `KEEP(*(.isr_vector))` 之后，为什么 `readelf -S` 还能看到 `.isr_vector` 这个段？
3. 你一个数组都没加，链接却报 `region 'RAM' overflowed by 4616 bytes`，最可能改了图纸哪一行？
4. 带初值的全局变量放进 `.ccmram`，图纸三行都写对了（`MEMORY` 加地块、`SECTIONS` 加房间、`AT> FLASH` 也不漏），上电读到的为什么还是随机值？

<details><summary><b>参考答案（先自己想完再展开）</b></summary>

1. 实测 `VMA=0x20000000`（程序运行时的住址，CPU 的 `ldr` 按它寻址）、`LMA=0x08000218`（初值在 Flash 的寄存地址）。CPU 读 VMA，装载器与 `objcopy -O binary` 读 LMA；`_sidata = LOADADDR(.data)` 取的是 LMA。
2. 因为段名是**输入段被登记过的痕迹**，`--gc-sections` 回收的是段里的**内容**，不是输出段目录里那一行。尺寸 0 的 `.isr_vector` 是一具空壳：`PROGBITS` 还在、`Size` 从 `000188` 变 `000000`。
3. `_Min_Stack_Size`（或 `_Min_Heap_Size`）。检查段只记账不占货，实测：`0x400 → 0x20000` 之后点名 `._user_heap_stack`，`RAM 135688 B = 103.52%`，`135688 − 131072 = 4616`。
4. 图纸单方面开了房间，**启动文件里没有对应的第二条拷贝循环**。实测 `grep -c` 数启动文件符号引用：`_sidata` 出现 3 次、`_siccm` 出现 0 次；`Reset_Handler` 反汇编只有一对 `ldr/str`。初值安安静静待在 Flash，没人来取。

</details>

## 对照表：本章概念 → 仓库落点

| 本章说的 | 仓库里哪一行 |
|---|---|
| 136 行图纸本体 | [stm32f407xx.ld](https://github.com/zhuguang-ZFG/mcu/blob/main/code/stm32/00-blink/stm32f407xx.ld)（关键行：`:16` `_estack`、`:24/28` MEMORY、`:38` KEEP、`:91` `_sidata`、`:100` `AT> FLASH`、`:117-123` 检查段） |
| 六个门牌被谁读走 | `startup_stm32f407xx.s:23-27`（`.global`）、`:48-51`（搬运）、`:64-65`（清零） |
| 六刀与实测输出 | `code/toolchain/03-linker/probe.sh`（`keep/at/overflow/flags/ccm/trace`） |
| 标本的三个变量 | `code/toolchain/03-linker/link_probe.c`（4 + 4100 + 1536 = 5640 的出处） |
| 向量表第 0/1 项的含义 | [B2 第五刀](02-elf.md)、[B4 第一节](04-startup.md) |
| CCM 只接 CPU | [S1 架构总览](../stm32/01-arch.md) 的总线矩阵动画、[S8 DMA](../stm32/08-dma.md) 的翻车实验 |

## 你做到了

- 一张 136 行的图纸从天书变成能逐行批改的东西：圈地、分房、留门牌，三件事各管一段；
- 见过三个"链接器不报错但固件是错的"现场：空壳 `.isr_vector`、`_sidata == _sdata`、orphan 到 `0x20000004` 的 `.ccmram`；
- 会用手算复核工具链：`4 + 4100 + 1536 = 5640 → overflowed by 3592`、`0x10000000 − 0x08000000 + 16 = 134,217,744`；
- 知道"图纸与启动文件是一套榫卯"：单方面加房间，机器会安静地给你一个错答案。

开场那句「图纸的力量不在语法，在契约」现在有了三个现场作证：不报错的空壳向量表、不报错的错位门牌、不报错的孤儿段。链接器沉默的地方，正是图纸替你扛住的地方；它扛不住时，就安静地给你一个错答案。

<div class="achievement">
✅ 下一站：<a href="04-startup.html">B4 启动过程</a>。本章发的六块门牌，看施工队怎么一条条读回去：上电到 <code>main</code> 之间的每一条指令。
</div>

## 附录：工程完整源码

标本本体（`.data`/`.bss`/`.ccmram` 三类住户，正文所有字节数出自它和 `../../stm32/00-blink`）：

<<< ../../code/toolchain/03-linker/link_probe.c

一条命令跑完六刀（每刀的 `sed` diff、报错原文、换算式都在这里）：

<<< ../../code/toolchain/03-linker/probe.sh

---
title: B1 四步构建：从 main.c 到机器码
status: done
difficulty: 2
minutes: 30
---

# B1 四步构建：预处理→编译→汇编→链接

> 🎯 `make` 一秒跑完的事，拆开是四道工序：预处理展开宏、编译生成汇编、汇编产出机器码、链接拼成固件。会拆就会查——90% 的"莫名编译错误"都能定位到具体某一环。

## 本章精髓

1. gcc 是"调度员"不是"全能选手"：它按后缀名和参数把活分包给 cc1/as/collect2（ld），`-###` 参数能把它的心里话全打印出来。
2. 每一步都产出一个可检查的中间文件：`.i`（纯 C）、`.s`（汇编）、`.o`（可重定位目标）、`.elf`（可执行）。
3. "头文件找不到"是预处理的事，"undefined reference"是链接的事：**报错阶段=嫌疑人范围**。

- **能理解**：亲手把 `main.c`（65 行）喂给 `-E`，看它膨胀成 1575 行，并在里面找到被摊平的 `RCC_BASE` 宏。
- **能用**：拿到任何一条编译报错，先看关键字（`fatal error: ... No such file` / `error: expected ...` / `undefined reference`）就能报出阶段。

## 先修

- [B0 工具链](00-toolchain.md)：`arm-none-eabi-gcc` 必须在 `PATH` 里（本机实测版本 15.2.1 / xPack）。

## 先跑起来（10 分钟 quick win）

跑之前先押两个数：你那份几十行的主源文件，预处理全部展开后会有几百行还是几千行？再押汇编那份又是多少？两个数都写下来，误差通常以倍数计。

```bash
cd code/toolchain/01-four-steps
sh probe.sh steps      # 只走四步，build/ 里留下 .i/.s/.o/.elf 全套证据
```

标本是 `code/stm32/00-blink` 的真实工程（`main.c` + 启动文件 + 链接脚本），不需要开发板。跑完你会看到三行关键数字：`main.i` 1575 行、`main.s` 3757 行、`.text` 从地址 0 变成 `0x08000188`。

再看三个报错现场：

```bash
sh probe.sh errors     # 预处理/编译/链接 各制造一个错误，原文对照
```

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 调度员 gcc | `-###` 打印内部分工；`-save-temps` 一键留证据 | 库解析 |
| 预处理 | 宏展开/#include 嵌套/条件编译；`#define` 与 const 之争 | 代码分析 |
| 编译与优化 | cc1 干的事；`-O0/-O2` 汇编对照入口（C3 联动） | 代码分析 |
| 汇编与目标文件 | .o 的"半成品"状态：符号还没地址（重定位预告） | 代码分析 |
| 链接 | 符号决议 + 重定位 + 按脚本排座（B3 深讲） | 库解析 |

## 一、调度员 gcc：`-###` 看它把活分给谁

先把整条流水线画出来：一份 65 行的 `main.c` 是怎样在四道工序里变成能烧进 Flash 的 `.elf`。

![B1 四步构建流水线动画](/anim/build-four-steps.svg)

`arm-none-eabi-gcc` 本身不编译任何代码。它读参数、查后缀、然后 fork 出真正的工具。加 `-###` 让它**只打印不执行**，内部分工一目了然（本机实测，路径已截断）：

```text
$ arm-none-eabi-gcc -### -E -mcpu=cortex-m4 -mthumb main.c -o main.i
 ".../libexec/gcc/arm-none-eabi/15.2.1/cc1.exe" ... -E ... -o main.i      # 预处理也是 cc1 干的

$ arm-none-eabi-gcc -### -c -mcpu=cortex-m4 -mthumb main.c -o main.o
 ".../libexec/gcc/arm-none-eabi/15.2.1/cc1.exe" ... -o /tmp/ccXXXX.s     # C → 汇编
 ".../arm-none-eabi/bin/as.exe" ... -o main.o                            # 汇编 → 目标文件

$ arm-none-eabi-gcc main.o startup.o -T stm32f407xx.ld -o blink.elf
 ".../libexec/gcc/arm-none-eabi/15.2.1/collect2.exe" ...                 # 由它再去调 ld
```

四条事实：

1. **预处理不是独立程序**。老教程说的 `cpp` 只是个壳，现代 GCC 里预处理和编译都是 `cc1`，靠 `-E`/`-S` 开关切换输出。
2. `-c` 一步其实跑了**两个**工具（cc1 + as），所以"编译"和"汇编"在命令行上能合并，但概念上仍是两道工序。
3. 链接由 `collect2` 代理：它负责收拾构造函数表（`__libc_init_array` 之类）再调 `ld`。所以链接报错里署名 `ld.exe`。
4. `-###` 顺带把 `COMPILER_PATH`/`LIBRARY_PATH` 打出来，找不到 `-lm` 或库版本串味时，这两行是第一个证据。

想一键留证据，不用记四条命令：`-save-temps` 会把 `.i/.s/.o` 自动堆在当前目录，`make` 的构建目录里立刻多出全套中间产物。

## 二、第 1 步：预处理 `-E`——宏在纸上摊平

`-E` 只做三件事：展开 `#include`、替换宏、按条件编译裁剪。输出仍是 C 源码（带 `# 行号 "文件"` 标记，给调试器认行用的）。

```bash
arm-none-eabi-gcc -E main.c -o main.i
```

实测：**65 行 → 1575 行**。多出来的 1510 行全是 `#include <stdint.h>` 等头文件的内容。打开 `main.i` 找 `main`，签名没变，但宏全没了：

```c
/* main.i 第 1556 行 */
int main(void)
```

更有意思的是源码里的 `RCC_BASE`，它在 `main.i` 第 1533 行还留了个 `#define`，但**用到它的地方已经摊成了纯算术式**：

```c
/* main.i 第 1559 行：源码里那行 RCC->AHB1ENR |= RCC_AHB1ENR_GPIOFEN; */
(*(volatile uint32_t *)(((0x40000000UL + 0x00020000UL) + 0x3800UL) + 0x30UL)) |= (1UL << 5);
```

这就是"宏只是文本替换"的实物：`0x40000000 + 0x20000 + 0x3800 + 0x30` 加法是留给编译器的活（常量折叠），`1UL << 5` 同理。**指针、volatile、位运算的语义从这一行开始就已经确定**。后面两步只是在"翻译"它。

## 三、第 2 步：编译 `-S`——C 变成汇编

`-S` 让 cc1 停在汇编层。它会做语法检查、类型检查、优化，然后吐出目标架构的汇编：

```bash
arm-none-eabi-gcc -S main.i -o main.s      # 实测 3757 行
```

`main` 的开场（本机实测节选）：

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

三点可验证的观察：

- `orr r3, r3, #32`：源码的 `|= (1UL << 5)` 被常量折叠成 `#32`。**读-改-写**在汇编里看得一清二楚：先 `ldr` 读、再 `orr` 改、最后 `str` 写。
- 为什么是"读-改-写"而不是一条原子指令？因为 C 里写的就是 `|=`。想避免（S3 讲过的翻车），要在**外设侧**换原子入口，这是后话。
- 地址 `0x40023830` 没出现在指令里，而是被塞进"字面池"（`.L6`），用 `ldr r3, .L6` 取。ARM 的立即数字段装不下 32 位地址，只能这么干。

`-O0` 下函数序言固定存在（`push {r7, lr}` + `add r7, sp, #0`，为了调试时栈回溯方便）；换 `-O2` 这两条会消失，这就是 C3 里"优化等级改变汇编"的入口。

## 四、第 3 步：汇编 `-c`——半成品 `.o`

```bash
arm-none-eabi-gcc -c main.s -o main.o
```

`.o` 是**可重定位目标文件**：机器码有了，但**地址还没有**。两条证据：

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

- `nm` 里的 `U` 表示"未定义符号"（本文件引用了、但定义在别处，等链接器补地址）。`main.o` 里**一个 `U` 都没有**，因为外设访问是硬编码地址常量，不需要符号决议。但 `startup_stm32f407xx.o` 里有一堆 `U`：`_sidata` / `_sdata` / `_edata` / `_sbss` / `_ebss` / `_estack`（段边界符号，链接脚本里定义）加 `main`（应用里定义），那些才是链接器的活。
- `objdump -h` 的地址栏是 `00000000`。这就是"可重定位"：`.text` 现在只是个 0xa8 字节的块，**将来放哪还没定**。

`nm` 的符号类型表（记住三个就够）：`T/t` = 代码段（大写全局、小写局部），`U` = 未定义（要别人给），`W` = 弱符号（可被覆盖）。

## 五、第 4 步：链接——决议符号 + 按脚本排座

```bash
arm-none-eabi-gcc main.o startup_stm32f407xx.o \
    -T stm32f407xx.ld -nostartfiles -o blink.elf
```

链接器（ld）做两件事：**符号决议**（把 `U` 一个个对上定义）+ **重定位**（按链接脚本把每个段放到具体地址，再把代码里的地址占位符填实）。

实测结果：

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

读法：

- **VMA（Virtual Memory Address）** = 运行时的地址。`.isr_vector` 和 `.text` 在 `0x0800_0000` 段（Flash），`.data`/`.bss` 在 `0x2000_0000` 段（SRAM）。这就是链接脚本把"哪块东西放哪块存储"焊死的效果，B3 整章讲这个。
- `text 660` = 392（向量表）+ 268（代码）。`bss 1536` 是 `._user_heap_stack` 预留的栈/堆空间，不占 Flash。
- `Reset_Handler` 是 **W（弱符号）**：启动文件里给了默认实现，用户可以覆盖。芯片复位后 CPU 从 `0x0800_0000` 取向量表第 2 个字跳到这里。
- `main` 的地址是 `080001aa`：**最低位是 1**。这不是错位：Cortex-M 只跑 Thumb 指令，函数符号地址的最低位 1 是"这是 Thumb 代码"的标记位。

到这里，四道工序走完：一份 65 行的 C 源码变成了一个能烧进 Flash 的 `.elf`。

## 报错分诊：三个现场实测

`sh probe.sh errors` 会故意制造三个错误，报错原文（本机实测）如下，**只看关键字就能定位阶段**：

| 阶段 | 关键字 | 实测报错原文 |
|---|---|---|
| 预处理 | `fatal error: ... No such file or directory` | `bad_pp.c:1:10: fatal error: no_such_header_xyz.h: No such file or directory` |
| 编译 | `error: expected ...` | `bad_cc.c:1:22: error: expected expression before ';' token` |
| 链接 | `undefined reference to ...` | `ld.exe: bad_ld.o: in function 'main': bad_ld.c:2:(.text+0x4): undefined reference to 'SystemInit'` |

三点：

1. **`fatal error` 只在预处理阶段出现**，预处理一旦失败就直接停，连语法分析都到不了。
2. **`error:` 是编译期语法/类型检查**，行号精确到列（`1:22`）。
3. **`undefined reference` 一定是链接期**，此时**编译已经全部通过**。修法是"补定义/补 `.o`/补库"，不是去改语法。上面这条报错还附带了 `warning: cannot find entry symbol Reset_Handler`，因为 `-nostartfiles` 没给启动文件，链接器找不到入口，这正说明"链接阶段在管符号和入口"。

## 附录：工程完整源码

本章取证工程 `code/toolchain/01-four-steps/`（`sh probe.sh` 直接跑通，需工具链在 `PATH`）：

**probe.sh**（四步 + 三错误现场，全自动取证）：

<<< ../../code/toolchain/01-four-steps/probe.sh

**被构建的标本** `code/stm32/00-blink/main.c`（B1 全篇的输出都由它而来）：

<<< ../../code/stm32/00-blink/main.c

## 记忆锚点

::: tip 一句话记住
**E、S、c、T 四步走：-E 出 .i，-S 出 .s，-c 出 .o，-T 定格局（链接脚本）。** 报错先问：死在哪一步？
:::

**延伸**：四步构建的工具链全景见 [B0](00-toolchain.md)；链接脚本详解见 [B3](03-linker-script.md)；ELF 产物解剖见 [B2](02-elf.md)。

## 实物实验

- **无板（本机已实测）**：`cd code/toolchain/01-four-steps && sh probe.sh`，四步输出与本文数字逐条对上（`main.i` 1575 行、`.text` 起始 `0x08000188`、`size` text=660）。
- **无板（进阶）**：把 `CFLAGS` 里的 `-O0` 改成 `-O2` 再跑 `sh probe.sh steps`，对比 `main.s`：函数序言 `push {r7, lr}` 消失，开时钟那三行 `ldr/orr/str` 可能被合并，亲手看优化等级如何改写汇编。
- **板上（可选，肉眼现象待回填）**：`cd code/stm32/00-blink && make flash`，PF6 红灯亮，那盏灯就是本章四步流水线的最终产物。

## 常见坑

- **把链接错当编译错**：`undefined reference to 'SystemInit'` 是链接阶段缺符号，不是语法问题，补定义或补 .o。
- **多文件忘了都传给链接器**：只链接 main.o，启动文件的符号全缺；Makefile 的 OBJS 列表就是干这个的。
- **汇编器参数漏 `-mcpu/-mthumb`**：.s 文件也走 gcc 调度，MCU 参数少了照样报错。
- **只 `-E` 就以为看到了真相**：`main.i` 里 `#define` 行还在（第 1533 行），但使用处已摊平，要看展开结果，得找**使用处**，不是找 `#define`。
- **以为 `.o` 里能看到最终地址**：`.o` 的地址栏永远是 0。想核对地址，只能看 `.elf`（`objdump -h` / `nm`）。

## 短自测

**1. `-E` 之后 `main.i` 从 65 行涨到 1575 行，多出来的是什么？**

<details><summary>答案</summary>

`#include <stdint.h>` 等头文件被整份贴进来的内容，加上宏展开后变长的行。预处理**只做文本层面的三件事**：展开 include、替换宏、按条件编译裁剪，不检查语法，更不生成任何机器码。

</details>

**2. `nm main.o` 一个 `U` 符号都没有，为什么？**

<details><summary>答案</summary>

因为 `main.c` 里的外设访问全是**硬编码地址常量**（`0x40023830` 等），不需要符号决议。汇编里那些地址走"字面池"（`ldr r3, .L6`）取常量，不是 `U` 引用。对比 `startup_stm32f407xx.o`：那里有 `U _sidata`、`U _sdata`、`U _edata`、`U _sbss`、`U _ebss`、`U _estack`（链接脚本负责定义）和 `U main`，才需要链接器去别处找定义。

</details>

**3. `undefined reference to 'SystemInit'` 死在哪个阶段？怎么修？**

<details><summary>答案</summary>

链接阶段。编译已经全部通过，问题是"某个符号被引用了却没人定义"。修法三选一：补上实现、把定义它的 `.o` 加进链接命令、或链接对应的库（`.a`）。改语法是南辕北辙。

</details>

**4. `-c` 之后 `objdump -h main.o` 里 `.text` 的地址栏是 0，为什么？**

<details><summary>答案</summary>

`.o` 是**可重定位**目标文件：代码块已经生成，但"放哪个地址"还没决定。地址由链接阶段按链接脚本分配（本例 `.text` 最终落在 `0x08000188`）。这也是为什么只有 `.elf` 才能查最终地址。

</details>

## 对照表：本章概念 → 仓库落点

| 概念 | 仓库落点 |
|---|---|
| 四步流水线的自动化脚本 | `code/toolchain/01-four-steps/probe.sh`（32–72 行 `steps`） |
| 预处理展开对照（65 → 1575 行） | 同上，第 1 步（35–43 行） |
| `main` 的汇编序言与开时钟的读-改-写（`ldr`/`ldr`/`orr`/`str`） | 同上，第 2 步（45–50 行） |
| `.o` 重定位状态（地址栏 = 0）与 `U` 符号对照 | 同上，第 3 步（52–61 行） |
| 段 VMA 与 `size` 汇总 | 同上，第 4 步（64–71 行） |
| 三个报错现场原文 | 同上，`errors`（74–109 行） |
| 被构建的标本源码 | `code/stm32/00-blink/main.c` |

## 你做到了

- 亲手走完四道工序，每步留证；
- 编译报错能按阶段定位嫌疑人。

开场说 make 一秒跑完四道工序，这一秒你现在拆开看过了：宏展开后的上千行、还没住址的目标文件、最后才拿到门牌的固件。下次报错，先问它发生在哪一环，嫌疑人名单立刻从四个缩到一个。

<div class="achievement">
✅ 下一站：<a href="02-elf.html">B2 ELF 解剖</a>：readelf/objdump 实拆一个固件，段与节不再傻傻分不清。
</div>

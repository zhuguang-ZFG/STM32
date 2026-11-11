# 03-volatile：不需要开发板的 volatile 取证工程

C3 章的配套工程。别人讲 volatile 给结论，这里给**汇编**：同一段源码，`-O0` 与 `-O2`、加与不加 `volatile`，四条路径的汇编差异全部可复现。

| 文件 | 角色 | 详解章节 |
|---|---|---|
| `opt_probe.c` | 四个现场：轮询 / 延时 / 写合并 / 共享标志 | [C3 volatile](../../../docs/c/03-volatile.md) |
| `Makefile` | `make asm O=2` 出汇编，`make run` 看行为 | [B1 四步构建](../../../docs/build/01-four-steps.md) |

## 构建与取证

装了 make：

```bash
make asm O=2      # → opt_probe.O2.s（宿主 x86-64）
make asm-arm      # → opt_probe.m4.O0.s / opt_probe.m4.O2.s（Cortex-M4）
make run          # 只跑不会死等/不会段错误的现场
```

没装 make 就用单行命令（本章所有汇编引证出自这四条）：

```bash
gcc -std=c11 -Wall -Wextra -O2 -S -o opt_probe.O2.s opt_probe.c
gcc -std=c11 -Wall -Wextra -O0 -S -o opt_probe.O0.s opt_probe.c
arm-none-eabi-gcc -std=c11 -Wall -Wextra -mcpu=cortex-m4 -mthumb -O2 -S -o opt_probe.m4.O2.s opt_probe.c
arm-none-eabi-gcc -std=c11 -Wall -Wextra -mcpu=cortex-m4 -mthumb -O0 -S -o opt_probe.m4.O0.s opt_probe.c
```

## 本机实测记录

环境：MinGW-Builds **gcc 16.1.0**（x86_64-posix-seh）+ binutils objdump 2.46；交叉侧 **xPack GNU Arm Embedded GCC 15.2.1 20251203**（`-mcpu=cortex-m4 -mthumb`）。Windows 10.0.26200，2026-10-06。四套命令均 `-std=c11 -Wall -Wextra` **零告警**。

```console
$ gcc -std=c11 -Wall -Wextra -O2 -o probe opt_probe.c && ./probe
现场4：4 次 xor 之后 shared_flag = 0（值对，但每一步都不是原子的）
现场2：delay_volatile(1000000) 真的耗了时间
现场3：cfg_plain 与 cfg_volatile 的差别只能从汇编看——make asm O=2
```

Cortex-M4 侧 `-O2` 的关键片段（`opt_probe.m4.O2.s` 原文，注释为本书所加；`.L` 标签编号按你的工具链版本可能不同）：

```asm
@ delay_plain：整个函数就是一条返回——你的"延时"根本没存在过
  bx      lr

@ poll_plain：只读一次，判不到位就原地死转
  ldr     r3, .L5
  ldr     r3, [r3]
  lsls    r3, r3, #31
  bpl     .L3          @ bit0=0 → 跳 .L3
  movs    r0, #42
  bx      lr
.L3:
  b       .L3          @ 再也不看那块内存

@ poll_volatile：每圈一次真实 ldr
.L8:
  ldr     r3, [r2, #4]
  lsls    r3, r3, #31
  bpl     .L8
  movs    r0, #42
  bx      lr

@ cfg_plain：三次 |= 并成一次访存（M4 没有读-改-写单指令，所以是 ldr/orr/str）
  ldr     r3, [r0]
  orr     r3, r3, #7
  str     r3, [r0]
  bx      lr

@ cfg_volatile：三组 ldr/orr/str，访存次数 = 源码写次数
  ldr     r3, [r0]
  orr     r3, r3, #1
  str     r3, [r0]
  ...（#2、#4 各一组）

@ isr_toggle：volatile 保住了访存，但读-改-写在 M4 上明晃晃是三条
  ldr     r3, [r2, #8]
  eor     r3, r3, #1
  str     r3, [r2, #8]
  bx      lr
```

x86-64 与 Cortex-M4 的差别只在指令形式：合并、删除、缓存这三项优化**两边一模一样**——同一个优化器、同一条 as-if 规则。

## 与 00-blink 的对照：六个变体各自挡住什么

正文"实物实验"要改 `code/stm32/00-blink` 的 `-O` 档，这里先把六个组合在 **arm-none-eabi-gcc 15.2.1 / `-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard` / `-O2 -Wall -Wextra`** 下实测出来（`objdump -d` 看 `main`，`delay` 被内联进去）：

```bash
sh blink-variants.sh          # → blink-variants/{A..F}.c 与逐个 main 反汇编
```

| 变体 | 寄存器宏 `volatile` | `delay` 参数 `volatile` | 循环体 `nop` | `-O2` 下 main 的长相 | 灯 |
|---|---|---|---|---|---|
| **A**（仓库现状） | 有 | 有 | 有 | 正常：先 `str [r2,#0x830]` 开时钟，再配 MODER | 闪 |
| **B** | 有 | **无** | 有 | 与 A 几乎相同，循环仍在（`nop / subs / bne`） | 闪 |
| **C** | 有 | **无** | **无** | 延时消失：`str [r3,#0x418]`（BSRR 亮）紧接 `str [r3,#0x418]`（BSRR 灭）`b` 回开头 | 不闪 |
| **D** | 有 | 有 | **无** | 循环保留，但计数在寄存器 r3（没有 `ldr/str`） | 闪 |
| **F** | **无** | 有 | 有 | 写还在，但**顺序倒了**：`ldr [r1,#0x400]`（读 GPIOF_MODER）排在 `str [r2,#0x830]`（开 GPIOF 时钟）**之前** | 未知——时钟没开就访问 GPIOF |
| **E** | **无** | **无** | **无** | `main:` 只有一条 `b.n 0`——**所有外设写被当死 store 删光** | 全黑，芯片啥也没干 |

四条值得记住的结论：

1. **只去掉 `delay` 参数的 `volatile` 是看不到"灯不闪"的**（B 行）——`__asm__ volatile ("nop")` 已经把副作用钉住了。想复现翻车得连 `nop` 一起删（C 行）。`volatile` 对象与 `asm volatile` 语句是两套独立机制，这就是"两道防线"的意思。
2. **寄存器宏比 `delay` 参数重要得多**：F 行只是漏了宏里的一个词，配置顺序就倒了——`RCC_AHB1ENR` 的写被推到 `GPIOF_MODER` 的读后面。在真芯片上这意味着"给还没上时钟的外设发读写"。
3. **E 行是"删除死 store"授权用在外设上的极端形态**：整段 `main` 塌成一条自跳转。别把这条当定律——删不删、重排到哪，取决于优化器当次能证明多少，换 `-O` 档或工具链版本就可能不一样。**所以合同必须写在源码里，而不是指望编译器今天心情好。**
4. **D 行顺带暴露了 `volatile` 局部变量的真相**：`delay` 是 `static` 且被内联进 `main`，参数计数就留在寄存器 r3；本工程的 `delay_volatile` 是外部函数、单独编译，参数落 `[sp,#4]` 每圈访存。**`volatile` 局部量地址未逃逸时可以被寄存器化**是真实存在的优化——它保的是"每次使用都可见"，不是"必须占一块内存"。MMIO 不受这条影响：地址是硬编码的，编译器无处可藏。

## 与开发板的对照

上表的 C 行是**编译期**证据（本机已实测）；**板上肉眼现象本轮未跑**——本机当前没有接 STM32F407 与 ST-Link。想上板复现，改 `code/stm32/00-blink`（默认 `-O0 -g3`）：

1. `CFLAGS` 里的 `-O0` 改 `-O2`，并把 `main.c:39` 的 `volatile` 与 `main.c:42` 的 `__asm__ volatile ("nop");` **一起**去掉（只去掉前者对应 B 行，灯照闪）；
2. `make flash` —— 红灯不再闪（两条 `BSRR` 写相邻，亮灭之间几乎零间隔）；
3. 只把 `volatile` 加回去、`nop` 仍删掉 → `-O2` 灯照闪（D 行）。

> 状态：宿主 gcc 与 arm-none-eabi-gcc 两套取证均本机实测通过（含上表四变体）；板上三步为编译期推论，**待上板回填**——欢迎你烧录后把现象/问题提到 Issue。


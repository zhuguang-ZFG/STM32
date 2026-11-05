---
title: C6 调用约定与栈帧
status: done
difficulty: 3
minutes: 45
---

# C6 调用约定与栈帧：一次函数调用的全程直播

> 🎯 参数装 r0–r3、多余的走栈、返回地址进 lr、返回值回 r0——函数调用的全部秘密就这四条。

## 本章精髓

1. 函数凭什么"调用完就回来"？`bl` 把返回地址写进 lr；非叶子函数把 lr 压栈，收尾时 `pop {…, pc}` 直接弹回程序计数器。
2. 参数凭什么"送得到"？AAPCS 铁律：r0–r3 装前 4 个、第 5 个起走栈、64 位占偶奇寄存器对、硬浮点走 d0–d7。
3. 局部变量凭什么"用完自动回收"？栈帧随 sp 移动而生灭，分配与释放的全部成本就是改一根指针。

- **能理解**：拿 `sum6` 的 `ldr r2, [sp]`、`mix` 调用方不写的 r1、`non_leaf` 的 `push {r4, lr}` … `pop {r4, pc}` 三段真实汇编，逐条对到 ABI 规则上。
- **能用**：给你一段 Cortex-M 的 `-O2` 反汇编，能说出参数从哪进、栈帧多大、返回地址压在栈上哪个字，[S16 崩溃定位](../stm32/16-debug-hardfault.md)要用的就是这个本事。

## 先修

- [C4 结构体与 ABI](04-struct-abi.md)：数据在内存里怎么排；本章讲调用发生时数据怎么进函数。
- [C5 函数指针](05-func-pointer.md)：`blx r3` 决定"跳到哪"；本章回答"跳过去之后参数怎么进、栈帧怎么长"。
- [C1 内存模型](01-memory-model.md)：知道栈住在 SRAM 哪一端、往哪头长。
- [B4 启动过程](../build/04-startup.md) 可读可后补：知道复位后 sp 从哪来。

## 先跑起来（10 分钟 quick win）

```bash
cd code/c/06-abi-stack
sh probe.sh   # 宿主 gcc 真跑 9 条断言；arm-none-eabi-gcc 在 PATH 时附送 Cortex-M4 汇编核对
```

跑之前先押：那个非叶子函数只开了一个局部数组，它的一帧会吃掉多少字节？刚好等于数组大小，还是更多？多出来的部分又是谁？押完对第一行输出。

宿主侧（gcc 16.1.0 实测输出，每条都是真跑出来的数）：

```text
一帧吃掉的栈          = 64 字节（两次 sp 之差，含返回地址+保存寄存器+buf）
buf 距 sp(non_leaf)   = 32 字节
sum6(1,2,3,4,5,6)     = 21（第 5、6 个参数 5、6 是走栈送进去的）
add64(0x100000000, 0x200000001) = 0x300000001（64 位结果走寄存器对回来）
== 断言通过 9/9 ==
```

交叉侧（本机 PATH 里的 arm-none-eabi-gcc 10.3.1，`-mcpu=cortex-m4 -mfloat-abi=hard -O2 -S`）里找这三行，AAPCS 就长这样：

```text
add2:
	@ link register save eliminated.   " 叶子函数：连 lr 都不用存
	ldr	r2, [sp]                       " sum6：第 5 个参数从栈上取
	pop	{r4, pc}                       " non_leaf：返回地址直接弹进 PC
```

> 用哪几个寄存器接收栈上的值，是编译器的自由：10.3.1 给成 `ldr r2, [sp]`，别的版本可能是 `ldr r1, [sp]`。AAPCS 只承诺"前 4 个参数在 r0–r3，第 5 个起在栈上 `[sp]`/`[sp,#4]`"，剩下的它不管。本章引用的每一条汇编都是本机 10.3.1 实跑产物，行号对得上 `probe.sh`。

## 动画：栈帧的一生

四个阶段循环播放：① 参数装车（r0–r3）② `push {r4, lr}` 保护现场 ③ 局部变量占坑（`sub sp`）④ `pop {r4, pc}` 满血返回。

![函数调用栈帧动画](/anim/stack-frame.svg)

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 一、为什么需要"约定" | 编译器不止一家，没约定就无法互相调用；寄存器分工表逐行对证据 | 代码分析 |
| 二、参数落位铁律 | r0–r3 装前 4 个；sum6 的第 5、6 个走栈（`@ args = 8` / `strd` / `ldr [sp]`） | 代码分析 |
| 三、64 位与偶奇寄存器对 | add64 的 adds/adc 进位链；mix 跳过 r1 的调用方铁证 | 代码分析 |
| 四、硬浮点 ABI | double 走 d0/d1 不占 r0:r1；fpv4-sp 只有单精度 → `__aeabi_dadd` | 代码分析 |
| 五、栈帧解剖 | 非叶子 `push {r4, lr}` + `sub sp` … `pop {r4, pc}`；叶子 add2 对照 | 代码分析 |
| 六、把 ABI 落成字节账 | 宿主实测一帧 64 字节、buf 距 sp 32 字节；M4 上同一函数 24 字节 | 代码分析 |

## 一、为什么需要"约定"

启动文件里一行 `bl main` 为什么能成？编译器是 gcc，启动文件是手写汇编，两者从没见过面，能接上头全靠 **AAPCS**（Procedure Call Standard for the ARM Architecture）：ARM 公布的调用约定，gcc / clang / IAR / Keil 全都遵守。它规定四个问题：参数放哪、返回值放哪、哪些寄存器用完要复原、栈怎么对齐。

核心寄存器分工（每一行都能在本章 probe 里找到对应证据）：

| 寄存器 | 别名 | 职责 | 调完还有效吗 | 本章证据 |
|---|---|---|---|---|
| r0–r3 | a1–a4 | 前 4 个参数 / 临时scratch；r0（64 位 r0:r1）带回返回值 | 被调方随便改（调用方自保） | sum6/add64/mix 全段 |
| r4–r8、r10、r11 | v1–v8 | 长期变量 | 被调方想用就得先存后恢复 | non_leaf `push {r4, lr}` |
| r9 | v6/sb | 平台保留 | 被调方保存 | —— |
| r12 | ip | 链接器贴片用的 scratch | 被调方随便改 | —— |
| r13 | sp | 栈指针，公共接口处 8 字节对齐 | —— | probe.c 第 113 行对齐断言 |
| r14 | lr | 返回地址，`bl` 时硬件写入 | 每次调用都被覆盖 | non_leaf 必须 push 它 |
| r15 | pc | 程序计数器 | —— | `pop {r4, pc}` 改写它完成返回 |

说白了，约定 = 谁可以用、谁必须存、参数放哪、返回值放哪。约定之外没有魔法。

## 二、参数落位铁律：r0–r3 装前 4 个，第 5 个起走栈

`sum6` 有 6 个 int 参数（probe.c 第 40–44 行），r0–r3 只装得下 4 个。看被调方汇编（probe.sh 第 45–46 行取证输出）：

```asm
sum6:
	@ args = 8, pretend = 0, frame = 0
	@ frame_needed = 0, uses_anonymous_args = 0
	@ link register save eliminated.
	add	r1, r1, r0
	add	r2, r2, r1
	add	r3, r3, r2
	ldr	r2, [sp]        @ 第 5 个参数 e，从栈上取
	ldr	r0, [sp, #4]    @ 第 6 个参数 f
	add	r3, r3, r2
	add	r0, r0, r3
	bx	lr
```

- `@ args = 8` 是编译器注释：调用方在栈上放了 **8 字节**入参（两个 int），函数自己的帧却是 0（`frame = 0`）。
- 前 4 个参数就在 r0–r3 里，三条 `add` 直接加完；第 5、6 个用 `ldr r2, [sp]` / `ldr r0, [sp, #4]` 从栈上读回来。

调用方一侧（main 内，`bl sum6` 之前，build/probe.s 第 217–224 行；probe.sh 第 48–50 行取证）：

```asm
	movs	r3, #5
	movs	r2, #6
	strd	r3, r2, [sp]   @ 一条指令：5 → [sp]，6 → [sp,#4]
	movs	r2, #3
	subs	r4, r0, r2     @ 断言 add2 的返回值 ==3，与传参无关
	movs	r3, #4
	movs	r0, #1
	bl	sum6
```

`strd`（store double）一次把第 5、6 参数写上栈顶，与被调方的两条 `ldr` 严丝合缝。（细心的读者会发现 r1=2 没被重写：编译器在同一编译单元内知道 `add2` 不改 r1，就沿用了，这是对函数体内情的优化，跨模块调用时 ABI 不作此承诺。）

行为断言兜底：`sum6(1,2,3,4,5,6) = 21`（宿主 9/9 之一），**语义不因传参方式改变**，变的只是成本：栈传参多出内存写+内存读，寄存器传参零额外访存。性能敏感的接口，参数控制在 4 个以内。

## 三、64 位参数：必须落在偶奇寄存器对

`add64`（probe.c 第 47–51 行）两个 `long long`：

```asm
add64:
	@ args = 0
	adds	r0, r0, r2    @ 低 32 位相加，s 后缀更新进位标志
	adc	r1, r1, r3      @ 高 32 位 + 进位
	bx	lr
```

x 在 **r0:r1**、y 在 **r2:r3**，返回值也在 r0:r1。`adds`/`adc` 进位链就是"两个 32 位寄存器扮一个 64 位数"的铁证。宿主实测：`add64(0x100000000, 0x200000001) = 0x300000001`。

真正的反直觉点在 `mix(int tag, long long v)`（probe.c 第 53–57 行）：tag 占了 r0，v **不能**放 r1:r2，AAPCS 要求 64 位参数对齐到**偶数号**寄存器，于是 v 落 r2:r3，**r1 被跳过**。

- 被调方从没读过入参 r1：`mov r1, r0`（r1 只当返回值高半的暂存）、`adds r0, r0, r2`、`adc r1, r3, r1, asr #31`：读的入参只有 r0、r2、r3。
- 调用方铁证（`bl mix` 之前，probe.sh 第 55–60 行取证段）：

```asm
	movs	r2, #0     @ v 低 32 位
	movs	r3, #1     @ v 高 32 位 → v = 0x1_0000_0000
	movs	r0, #7     @ tag
	bl	mix        @ r1 压根没被赋值——这就是"跳过"
```

此刻 r1 里躺的是上一个函数的返回高半（垃圾值），而 mix 正确地对它视而不见。宿主断言：`mix(7, 0x100000000) = 0x100000007`。推论：给函数签名排序时把 64 位参数放前面、int 填后面，能少留寄存器空洞——ABI 不会替你重排。

## 四、硬浮点 ABI：double 走 d0/d1，不占 r0:r1

编译旗 `-mfpu=fpv4-sp-d16 -mfloat-abi=hard`（probe.sh 第 37 行）。hard 表示**浮点参数走 VFP 寄存器**：单精度 s0–s15、双精度 d0–d7。`add_d(double, double)`（probe.c 第 60–64 行）的汇编（build/probe.s 第 90–99 行）：

```asm
add_d:
	@ args = 0            @ 栈上参数 0 字节
	push	{r3, lr}
	vmov	r0, r1, d0    @ 把 d0 搬进内核寄存器对……
	vmov	r2, r3, d1    @ ……只是因为 fpv4-sp 只有单精度硬件，
	bl	__aeabi_dadd    @   double 加法得调软件库（它按 r0:r1/r2:r3 收参）
```

两个 double 是从 **d0、d1** 进来的，`vmov r0, r1, d0` 恰好证明了这一点；占 r0:r1 是被调的软件库 `__aeabi_dadd` 的内部约定，不是本函数的传参方式。对照：`-mfloat-abi=soft` 时 double 按 64 位整数规则直接走 r0:r1。两种 ABI 编出的目标文件**不能混链**（链接器会报 VFP 参数 mismatch）：这就是"ABI"三个字的分量。宿主断言：`add_d(0.5, 0.25) == 0.75`（9/9 之一）。

## 五、栈帧解剖：push {r4, lr} … pop {r4, pc}

`non_leaf`（probe.c 第 78–88 行）内部还要 `bl sink`、`bl add2`，每次 `bl` 都会覆盖 lr，所以 prologue 必须先把 lr 存起来。为什么还带着 r4？因为 `sink` 标了 `__attribute__((noipa)`（probe.c 第 70–76 行注释）：禁用一切过程间分析，调用方只能按 ABI 做最坏假定：r0–r3、r12 全被改写。想活过这次调用的值，只能放进被调方保存寄存器，r4 由此登场。

完整帧（probe.sh 第 62–63 行取证输出）：

```asm
non_leaf:
	push	{r4, lr}        @ 8 字节：保存 r4 与返回地址
	sub	sp, sp, #16     @ 16 字节：buf[16] 的家
	@ …
	bl	sink
	bl	add2
	pop	{r4, pc}        @ 恢复 r4，返回地址直接弹进 PC——连 bx lr 都省了
```

**返回地址弹进 PC** 是 Thumb-2 的经典收尾：弹栈与跳转合一。口诀里"lr 记着回家道"的下半场：回家不一定要经过 lr，可以直接进门。这个 Cortex-M4 帧 = push 8 + sub 16 = **24 字节**。

对照组 `add2`（probe.c 第 33–37 行）：叶子函数不调用任何人，编译器直接注释 `@ link register save eliminated.`，全身就 `add r0, r0, r1` + `bx lr` 两条指令。计数核对（probe.sh 第 66–70 行）：全文件 `push {r4, lr}` 恰出现 1 次、`pop {r4, pc}` 恰出现 1 次，正是 non_leaf 这一对；`strd , [sp]` 也恰 1 次，就是 sum6 那次的栈传参。

## 六、把抽象 ABI 落成字节账（宿主实测）

宿主 gcc 16.1.0（x86-64）真跑 non_leaf，探针打印（probe.c 第 115–121 行）：

| 量 | 实测值 |
|---|---|
| sp(main, 调用前) | `0x7d73dff980` |
| sp(non_leaf 体内) | `0x7d73dff940` |
| 一帧吃掉的栈 | **64 字节**（含返回地址 + 保存寄存器 + buf + 对齐填充） |
| buf 地址 | `0x7d73dff960` |
| buf 距 sp(non_leaf) | **32 字节** |

布局断言同步通过（probe.c 第 110–113 行）：sp 向下走（`sp_callee < sp_main`）、buf 落在本帧之内、帧差是 8 的倍数：AAPCS 要求公共接口处 sp **8 字节对齐**，主流桌面 ABI 同样有对齐条款。

注意口径：64 字节是宿主编译器的帧；**同一个 non_leaf 编到 Cortex-M4 是 24 字节**（第五节的 8+16）。字节账随目标与编译器而变，不变的是机制：**sp 一根指针的移动 = 分配与释放的全部成本**。

与前后章的呼应：

- [C5 函数指针](05-func-pointer.md)：函数指针在机器码层面是 `blx r3`，跳到寄存器里的地址；本章补的是跳过去之后"参数怎么进、帧怎么长"。传参规则与直接调用完全一致，函数指针才能与直调无缝互换。
- [S16 HardFault 与排错](../stm32/16-debug-hardfault.md)：HardFault 时硬件把 r0–r3、r12、lr、pc、xPSR 自动压进当前栈：反查崩溃行号，就是按本章的栈帧知识把那个 pc 从栈里挖出来。
- [F2 上下文切换](../rtos/freertos/02-context-switch.md)：切任务 = 把一整套寄存器现场换栈保存/恢复，机制与本章 prologue/epilogue 同源。

## 附录：工程完整源码

本章取证工程 `code/c/06-abi-stack/`（`sh probe.sh` 一条命令跑完，不需要开发板）：

**probe.c**（六个实验函数：add2 / sum6 / add64 / mix / add_d / non_leaf）：

<<< ../../code/c/06-abi-stack/probe.c

**probe.sh**（宿主编译运行 + 交叉汇编取证）：

<<< ../../code/c/06-abi-stack/probe.sh

## 记忆锚点

::: tip 一句话记住
**参数 r0 到 r3，多余的上栈找；64 位占偶奇对，r1 可以被跳掉；返回值 r0 里抱；r4–r11 谁用谁保管；lr 记着回家道，pop 进 pc 一把销。**
:::

## 实物实验

- **装备**：霸天虎板 + ST-Link + 第 0 章工程 + OpenOCD/GDB。
- **做法**：断点打在任一非叶子函数入口，`si` 单步过 prologue；每步 `info registers sp lr pc`，再 `x/4xw $sp` 看栈顶。
- **预期现象**（数字来自本章 Cortex-M4 汇编）：`push {r4, lr}` 后 sp 减 8，栈顶第二个字就是返回地址（lr 的拷贝）；`sub sp, #16` 后再减 16，整帧 24 字节；`pop {r4, pc}` 后 sp 复原，pc 精确落回 `bl` 的下一条指令。
- **进阶**：在 HardFault_Handler 里读硬件压栈帧的第 7 个字（偏移 24，即 stacked pc），对照 map 文件找崩溃行，完整流程见 [S16](../stm32/16-debug-hardfault.md)。
- 交叉引用：[实验中心 E02 待建](../lab/index.md)。

## 常见坑

- **误以为 `lr` 不用保存**：函数里再调函数（非叶子），第一次 `bl` 就把 lr 覆盖了，所以 non_leaf 的 prologue 一定有 `push {…, lr}`，而叶子 add2 才配拥有 `@ link register save eliminated.`。手写汇编忘了 push lr，返回时程序直接乱飞。
- **64 位参数落位想当然**：`mix(int, long long)` 的 long long 在 r2:r3 而不在 r1:r2，调试时按 r1 找值，找到的是上一个函数留下的垃圾（本章调用方汇编里 r1 残留 add64 的返回高半）。
- **中断里也在用同一个栈**：ISR 的硬件压栈发生在被中断者的栈上，栈预算要算上最坏中断嵌套，[F2 上下文切换](../rtos/freertos/02-context-switch.md)会回头算这笔账。
- **递归无界 = 栈溢出踩堆/全局区**：裸机没有 MMU 兜底，症状是"变量莫名其妙变了"，HardFault 都不一定报。
- **`main` 里 `return` 不会"回到命令行"**：裸机没有命令行可回；[B4 启动过程](../build/04-startup.md)里 main 返回后的去向是启动代码的死循环。

## 短自测

**1. `sum6` 的第 5、6 个参数怎么进函数？给出调用方与被调方双向证据。**

<details><summary>看答案</summary>

调用方：main 在 `bl sum6` 前用一条 `strd r3, r2, [sp]` 把 5 → `[sp]`、6 → `[sp,#4]` 写上栈（build/probe.s 第 224 行）。被调方：`sum6` 内 `ldr r2, [sp]` / `ldr r0, [sp, #4]` 取回，且编译器注释 `@ args = 8` 标明栈上入参 8 字节（自己的 `frame = 0`）。宿主断言 `sum6(1..6)=21` 通过。

</details>

**2. `mix(int tag, long long v)` 里 v 为什么在 r2:r3 而不是 r1:r2？此刻 r1 里是什么？**

<details><summary>看答案</summary>

AAPCS 要求 64 位参数落在**偶奇寄存器对**。tag 占了 r0 后，下一个可用的偶奇对是 r2:r3，r1 被跳过。调用方汇编（`movs r2, #0` / `movs r3, #1` / `movs r0, #7` / `bl mix`）从头到尾没写 r1，r1 里残留的是 add64 返回值的高半，mix 对它视而不见。

</details>

**3. 为什么 non_leaf 必须 `push lr`，而 add2 不用？各引一条证据。**

<details><summary>看答案</summary>

non_leaf 内部 `bl sink`、`bl add2`，任何一次 `bl` 都会覆盖 lr，不保存就回不了家，所以 prologue 有 `push {r4, lr}`。add2 是叶子函数（不调用任何人），lr 不会被覆盖，编译器直接注释 `@ link register save eliminated.`，全身只有 `add r0, r0, r1` + `bx lr`。

</details>

**4. `pop {r4, pc}` 一条指令完成了哪两件事？为什么能省掉 `bx lr`？**

<details><summary>看答案</summary>

① 从栈上恢复 r4（被调方保存寄存器复原）；② 把 prologue 存下的返回地址直接弹进 pc，弹栈与跳转合一，程序计数器被改写的瞬间就完成了返回，自然不需要再走 lr + `bx lr` 这条路。这是 Thumb-2 的经典收尾。

</details>

**5. 硬浮点 ABI 下 `add_d` 的两个 double 从哪进来？汇编里哪条指令能证明？**

<details><summary>看答案</summary>

从 d0、d1 进来（`-mfloat-abi=hard` 时浮点参数走 VFP 寄存器，不占 r0:r1，所以 `@ args = 0`）。证据是 `vmov r0, r1, d0` / `vmov r2, r3, d1`：编译器把 d0/d1 搬进内核寄存器，只是因为 fpv4-sp 没有双精度硬件，要调软件库 `__aeabi_dadd`。

</details>

## 对照表：本章概念 → 仓库落点

| 概念 | 仓库落点 |
|---|---|
| 叶子函数不保存 lr | `code/c/06-abi-stack/probe.c` 33-37 行；汇编取证 probe.sh 42-43 行 |
| 第 5、6 参数走栈（sum6） | probe.c 40-44 行；`@ args = 8` 与 `ldr [sp]` 见 probe.sh 45-46 行输出 |
| 调用方 strd 写栈传参 | probe.sh 第 48-50 行取证；build/probe.s 第 224 行（`strd r3, r2, [sp]`，main 内） |
| 64 位寄存器对 / adds+adc | probe.c 47-51 行；probe.sh 52-53 行输出 |
| r1 跳过（mix） | probe.c 53-57 行；调用方取证 probe.sh 55-60 行 |
| 硬浮点 d0/d1（add_d） | probe.c 60-64 行；编译旗见 probe.sh 37 行；汇编 build/probe.s 89-95 行 |
| noipa 迫使 r4 登场 | probe.c 70-76 行（sink 的 `__attribute__((noipa))` 注释） |
| 非叶子栈帧三件套 | probe.c 78-88 行；`push/sub … pop` 取证 probe.sh 62-63 行 |
| 帧字节账与对齐断言 | probe.c 94、110-121 行（一帧 64 字节、buf 距 sp 32 字节） |
| 9/9 行为断言 | probe.c 103-109、127 行 |
| push/pop 计数核对 | probe.sh 61-64 行（各恰 1 次） |

## 延伸阅读

9 条断言逐条对应的条款：

- **[\[C4\]](../reference/bibliography.md#toolchain)** AAPCS32 — r0–r3 传参、r4–r11 被调用者保存、64 位参数落偶奇寄存器对、公共接口处栈 8 字节对齐，全在"Procedure Call Standard"一节。

## 你做到了

- 看反汇编不再发怵：prologue/epilogue 一眼认出，`@ args = 8` 这种注释也会读了。
- 明白局部变量"自动回收"其实是 sp 一根指针的移动，一帧 24～64 字节的账自己会算。
- 能预言参数落位（包括 64 位跳过 r1 这种反直觉情况），并能拿汇编验证自己的预言。
- 给 [S16](../stm32/16-debug-hardfault.md) 的崩溃现场分析备好了全部读帧本领。

回到开场那四条口诀：参数装 r0–r3、多余的走栈、返回地址进 lr、返回值回 r0，现在每一条都有你亲手跑出来的汇编行作证。一次函数调用不再是黑盒，是一笔算得出的栈账。

<div class="achievement">
✅ 下一站：<a href="07-ub-misra.html">C7 未定义行为与 MISRA-C 精要</a>：看看约定管不到的"未定义行为"能野到什么程度；也可以拐去 <a href="../stm32/16-debug-hardfault.html">S16 HardFault 与排错</a>，把栈帧里的 PC 挖出来反查崩溃行号。
</div>

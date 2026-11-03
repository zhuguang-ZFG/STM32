---
title: S16 HardFault 与排错：崩溃现场的法医技术
status: done
difficulty: 3
minutes: 50
---

# S16 HardFault：崩溃现场的法医技术

> 🎯 程序跑着跑着不动了，灯不闪了，printf 沉默了——恭喜你遇到 HardFault。新手靠猜，法医靠证据：故障寄存器里写着"死因"，栈里躺着"案发现场"。

## 本章精髓

1. 故障是"异常升级"：MemManage / BusFault / UsageFault 没使能或处理不当就升级成 HardFault，HFSR 的 `FORCED` 位会告诉你：这是"升级案"，真凶要去 CFSR 里找。
2. 三份验尸报告：**CFSR**（可配置故障状态：19 个位逐位点名死因）、**BFAR**（总线故障的具体地址）、**MMFAR**（存储管理故障地址）。地址一指，凶手现形，但只有对应的 `BFARVALID` / `MMARVALID` 为 1 时才可信。
3. 栈帧即现场：异常进入时硬件压的 8 个字里有**案发时的 PC**。从栈里挖出 PC，用 `addr2line` 反查源码行：这是"死机"和"知道死在哪一行"的区别。

- **能理解**：看 naked `HardFault_Handler` 的反汇编：`tst.w lr, #4` / `ite eq` / `mrseq r0, MSP` / `mrsne r0, PSP`。短短四条指令就解决了"案发时用的是哪个栈"。
- **能用**：板子一死，先读 CFSR，再读栈帧 PC，`addr2line` 定位到行。所有裸机疑难，都按同一套流程破案。

## 先修

- [S4 中断与 NVIC](04-nvic-exti.md)：异常号、向量表、优先级，本章大量复用。
- [C6 调用约定与栈帧](../c/06-abi-stack.md)：`push {r4, lr}` 与"返回地址弹进 PC"是读懂本章汇编的前提。
- [B2 ELF 与 objdump](../build/02-elf.md)：`nm` / `objdump` / `addr2line` 的用法。

## 先跑起来（10 分钟 quick win）

```bash
cd code/stm32/16-debug-hardfault
sh probe.sh          # 宿主 274 条断言；工具链在 PATH 时附送 Cortex-M4 反汇编与 addr2line 全链路
```

输出里找这两行：

```text
== 断言通过 274/274 ==
  ----- 对账结果：逐位一致（39 条全中） -----
```

"逐位一致"指的是：本章代码里的 39 条故障寄存器位号（CFSR 19 位 + SHCSR 14 位 + HFSR 3 位，另有 3 条子寄存器基名），与 ST 官方 CMSIS 头文件 `core_cm4.h` **逐条比对、零差异**。后面正文里每一个位号都不是背出来的，是当场从官方头文件挖出来对过的。

在板上写一行 `*(volatile uint32_t*)0xFFFFFFFF = 0;` 就能触发 HardFault：第一次"按地址抓凶手"。

结案之前先押个真凶：把栈帧里抓到的 PC 交给 addr2line，报出来的那一行，一定是真凶本人吗？还是可能只是被牵连的邻居？押完往下读，看真凶指令和函数入口之间隔着什么。

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 故障家族 | HardFault / MemManage / BusFault / UsageFault 的升级关系 | 配置 |
| 验尸三寄存器 | SCB 版图；CFSR / HFSR / MMFAR / BFAR 的偏移与分工 | 配置 |
| CFSR 19 位 | MMFSR 6 + BFSR 7 + UFSR 6 逐位点名；两个"有效性位" | 库解析 |
| 栈帧取证 | MSP / PSP 判定（EXC_RETURN bit2）；8 个字里找 PC | 代码分析 |
| Handler 实现 | naked 汇编取栈指针 + C 侧抄报告的最小实现；四条指令的字节学与那个"工具链不拦"的位 | 代码分析 |
| addr2line 反查 | PC → 源码行；函数入口 vs 真凶指令的区别 | 代码分析 |
| 高频死因 | 空指针 / 未对齐 / 除零 / 爆栈 / 优先级五大命案 | 库解析 |

## 一、故障家族：四个异常，一个终点

Cortex-M4 有四个"故障"类异常。它们的异常号与 `IRQn` 枚举值（`stm32f407xx.h:67-75`）：

| 异常 | 异常号 | IRQn 枚举 | 向量表内偏移 |
|---|---|---|---|
| HardFault | 3 | **无**（见下） | 0x0C |
| MemManage | 4 | `MemoryManagement_IRQn = -12`（69 行） | 0x10 |
| BusFault | 5 | `BusFault_IRQn = -11`（70 行） | 0x14 |
| UsageFault | 6 | `UsageFault_IRQn = -10`（71 行） | 0x18 |

**第一处反直觉**：HardFault 的异常号是 3、排在 MemManage 前面，但 `IRQn_Type` 枚举里**故意没有它**：`stm32f407xx.h` 第 68 行是 `NonMaskableInt_IRQn = -14`，第 69 行直接跳到 `MemoryManagement_IRQn = -12`，中间的 `-13`（= 异常号 3）被整个省略了。原因是 CMSIS 的 `NVIC_SetPriority()` 只接受 `IRQn_Type`，省略它等于从类型层面禁止你给 HardFault 设优先级。HardFault 的优先级是**固定**的最高档：它不可屏蔽、不可设。

**第二处**：另外三个故障是"可配置"的。它们各自在 SHCSR 里有一个使能位，位号实测（`core_cm4.h:545-580`）：

```text
SHCSR:MEMFAULTENA 16
SHCSR:BUSFAULTENA 17
SHCSR:USGFAULTENA 18
```

关上时，对应的故障**不单独上报**，而是直接升级成 HardFault，这时 HFSR 的 `FORCED` 位会亮起来，告诉你"这是一起升级案，真凶在 CFSR 里"。所以看到 HardFault 不要先去翻 HardFault，先看 `FORCED`。

## 二、验尸三寄存器：SCB 版图

所有故障寄存器都挂在 `SCB`（System Control Block）下，基址 `0xE000ED00`。各寄存器偏移出自 `core_cm4.h:449-459`，下面是 probe 打印并已比对过的绝对地址：

```text
  SCB 基址            = 0xE000ED00
  SHCSR (使能开关)    = 0xE000ED24
  CFSR  (可配置故障)  = 0xE000ED28
  HFSR  (硬故障状态)  = 0xE000ED2C
  MMFAR (存储故障地址)= 0xE000ED34
  BFAR  (总线故障地址)= 0xE000ED38
```

分工很清楚：

- **CFSR**：`configurable fault status`，19 个位逐个点名死因。它管的是"可配置故障"，但 HardFault 升级上来时它**同样有内容**：真凶往往就在这。
- **HFSR**：`hard fault status`，只有 3 个位，定性用。
- **MMFAR / BFAR**：两个"现场地址"。BFAR 存总线故障的访问地址，MMFAR 存存储管理故障的地址。

**最关键的坑**：MMFAR / BFAR 里的地址**不是永远可信**。CFSR 里有两个专门的"有效性位"：`MMARVALID`(7) 和 `BFARVALID`(15)。只有它们为 1 时，对应的地址寄存器才保真。probe 里的解码示例：

```text
  CFSR = 0x00008200
    命中 2 位：PRECISERR + BFARVALID
    BFAR = 0x1FFFFFFF  （BFARVALID=1，这个地址可信）
  HFSR = 0x40000000 → FORCED —— 被升级：真凶在 CFSR 里，去查它
```

`0x00008200` 拆开看就是 bit9 + bit15：bit9 = `PRECISERR`（精确总线错误），bit15 = `BFARVALID`，两相印证，所以 `BFAR = 0x1FFFFFFF` 这个"访问了不存在的地址"结论站得住。

## 三、CFSR 19 位逐位点名

CFSR 是三个子寄存器拼成的（`core_cm4.h:616-684`）：低 8 位 MMFSR、次 8 位 BFSR、高 16 位 UFSR。probe 的表实测是 **MMFSR 6 位 + BFSR 7 位 + UFSR 6 位 = 19 位**（子寄存器的基名 `MEMFAULTSR`/`BUSFAULTSR`/`USGFAULTSR` 只占 3 条记录，不参与点名的位数）。

| 子寄存器 | 位 | 名字 | 白话 |
|---|---|---|---|
| MMFSR | 0 | `IACCVIOL` | 取指越权 |
| MMFSR | 1 | `DACCVIOL` | 访存越权 |
| MMFSR | 3 | `MUNSTKERR` | 出栈时存储管理错 |
| MMFSR | 4 | `MSTKERR` | 入栈时存储管理错 |
| MMFSR | 5 | `MLSPERR` | 懒浮点保存时出错 |
| MMFSR | 7 | `MMARVALID` | **MMFAR 可信** |
| BFSR | 8 | `IBUSERR` | 取指总线错 |
| BFSR | 9 | `PRECISERR` | 精确总线错（地址就是 BFAR） |
| BFSR | 10 | `IMPRECISERR` | 不精确总线错（地址不可信！） |
| BFSR | 11 | `UNSTKERR` | 出栈时总线错 |
| BFSR | 12 | `STKERR` | 入栈时总线错 |
| BFSR | 13 | `LSPERR` | 懒浮点保存时总线错 |
| BFSR | 15 | `BFARVALID` | **BFAR 可信** |
| UFSR | 16 | `UNDEFINSTR` | 未定义指令 |
| UFSR | 17 | `INVSTATE` | 非法状态（Thumb 位丢了） |
| UFSR | 18 | `INVPC` | 非法 PC |
| UFSR | 19 | `NOCP` | 用了没开的协处理器 |
| UFSR | 24 | `UNALIGNED` | 未对齐访问 |
| UFSR | 25 | `DIVBYZERO` | 除以零 |

全 1 解码（probe 实测，19 个名字全中）：

```text
  IACCVIOL + DACCVIOL + MUNSTKERR + MSTKERR + MLSPERR + MMARVALID
+ IBUSERR + PRECISERR + IMPRECISERR + UNSTKERR + STKERR + LSPERR + BFARVALID
+ UNDEFINSTR + INVSTATE + INVPC + NOCP + UNALIGNED + DIVBYZERO
```

**为什么这张表要一位一位对**：故障解码是枯燥的体力活，但位号记错一位，你整晚的推断方向就全歪了。probe 的 `--dump-positions` 把表导出成机器可读格式，`probe.sh` 用 `awk` 从官方头文件现挖同样的 39 条位号，两边 `diff`，**零差异**才算过。这就是"不许凭印象背位号"的工程做法。

## 四、栈帧取证：案发时用的是哪个栈

先看"崩溃破案"的整条流水线：案发、升级、取证、PC 对行号。

![HardFault 故障取证全流程动画](/anim/hardfault-forensics.svg)

异常进入时，硬件**自动**把 8 个寄存器压进当前栈（ARMv7-M 异常机制），probe 实测的版图（`fault_ctx.c:22-24` 的 `hw_frame_t`）：

```text
  偏移 0/4/8/12 = r0-r3，16 = r12，20 = lr，24 = pc，28 = xpsr（共 32 字节）
```

三个位置最关键：

- **偏移 20 = LR**：这是"从哪儿调用来的"，还原调用链靠它。
- **偏移 24 = PC**：**案发时正在执行的指令地址**，法医的主证据。
- **偏移 28 = xPSR**：其中的 IPSR 字段告诉你当时在哪个异常里。

问题来了：栈指针有两个（MSP 主栈、PSP 进程栈），硬件压的是**哪一个**？答案藏在异常进入时硬件写进 LR 的那个特殊值 `EXC_RETURN`（`core_cm4.h:1636-1641`）里：

```text
  0xFFFFFFF1 处理模式/MSP/无FPU | 0xFFFFFFF9 线程/MSP/无FPU
  0xFFFFFFFD 线程/PSP/无FPU    | 0xFFFFFFE1/E9/ED 同上但带 FPU 上下文
```

判据是 **bit2**：

- `bit2 = 0`（如 `0xFFFFFFF1`、`0xFFFFFFF9`）→ 案发时用 **MSP**（裸机主循环、中断嵌套）。
- `bit2 = 1`（如 `0xFFFFFFFD`）→ 案发时用 **PSP**（RTOS 任务）。

probe 实测样例：`EXC_RETURN = 0xFFFFFFFD → 案发时用 PSP（RTOS 任务栈），不带 FPU 上下文`。**拿错栈指针，读出来的 8 个字全是垃圾，后面所有推断都是假的**。这是 HardFault Handler 最容易写错的一处。

另外两个位也顺手用上：bit3（`0x8`）=0 表示案发时处于 handler 模式；bit4（`0x10`）=0 表示带 FPU 上下文（浮点寄存器也被压栈了，栈帧更长）。

## 五、Handler 实现：naked 汇编 + C 报告

写一个正确的 Handler，核心就是上面那一条判据。用 `naked` 属性让编译器别插桩，自己写那五条指令（`fault_ctx.c:50-61`）：

```c
__attribute__((naked))
void HardFault_Handler(void)
{
    __asm volatile(
        "tst   lr, #4            \n"  /* bit2 决定用哪个栈 */
        "ite   eq                \n"
        "mrseq r0, msp           \n"  /* eq：MSP */
        "mrsne r0, psp           \n"  /* ne：PSP */
        "b     hardfault_report  \n"  /* 交给 C 侧抄报告 */
    );
}
```

交叉编译后的真实反汇编（`probe.sh` 第 3 段输出）：

```text
08000070 <HardFault_Handler>:
 8000070:	f01e 0f04 	tst.w	lr, #4
 8000074:	bf0c      	ite	eq
 8000076:	f3ef 8008 	mrseq	r0, MSP
 800007a:	f3ef 8009 	mrsne	r0, PSP
 800007e:	f7ff bfbf 	b.w	8000000 <hardfault_report>
 8000082:	bf00      	nop
```

值得逐条读一遍：

- `tst.w lr, #4` 测 bit2，结果进标志位。
- `ite eq` 是 Thumb-2 的 `if-then-else` 块声明：它告诉后续两条指令"第一条按 eq 执行、第二条按 ne 执行"。**没有它，条件指令就是非法的**。
- 两条 `mrs` 分别读 MSP / PSP，结果都放进 `r0`，因为 `r0` 是 AAPCS 的第一个参数（见 [C6](../c/06-abi-stack.md)）。
- `b.w hardfault_report` 直接尾跳到 C 函数，`r0` 就是栈帧指针。

C 侧只做一件事：抄报告（`fault_ctx.c:27-48`），读四个 SCB 寄存器、从栈帧里取 LR/PC/xPSR，然后**死循环不动**：

```c
g_cfsr       = *(volatile uint32_t *)0xE000ED28UL;   /* CFSR  */
g_hfsr       = *(volatile uint32_t *)0xE000ED2CUL;   /* HFSR  */
g_mmfar      = *(volatile uint32_t *)0xE000ED34UL;   /* MMFAR */
g_bfar       = *(volatile uint32_t *)0xE000ED38UL;   /* BFAR  */
g_frame_lr   = frame[5];
g_frame_pc   = frame[6];                             /* ← 案发时的 PC */
g_frame_xpsr = frame[7];
```

现场全部落到 `volatile` 全局变量里，然后死等 GDB 来读，**故意不打印**。这是刻意的设计：故障上下文里跑 `printf` 这种复杂库函数，很可能触发二次故障，把唯一的现场也毁掉。

### 那四条指令的字节学：条件到底存在哪个词里

`probe.sh` 第 4 段把 Handler 单独编成裸二进制，逐字节拆开看。先看正确版和"把 ne 槽也写成 msp"的笔误版：

```text
00000000 <h_psp>:                     00000000 <h_msp>:
   0:	f01e 0f04 	tst.w	lr, #4           0:	f01e 0f04 	tst.w	lr, #4
   4:	bf0c      	ite	eq                 4:	bf0c      	ite	eq
   6:	f3ef 8008 	mrseq	r0, MSP            6:	f3ef 8008 	mrseq	r0, MSP
   a:	f3ef 8009 	mrsne	r0, PSP            a:	f3ef 8008 	mrsne	r0, MSP
   e:	4770      	bx	lr                   e:	4770      	bx	lr
```

两份机身各 16 字节，`cmp -l` 只报出一行（它给的是 octal）：

```text
  正确版 hex: 1ef0040f0cbfeff30880eff309807047
  笔误版 hex: 1ef0040f0cbfeff30880eff308807047
  差异字节数 = 1，明细：13  11  10
```

第 13 个字节从 octal `11`（0x09）变成 `10`（0x08），**整个语义差别就是一个位**。因为 MRS 的编码是 `f3ef 8<Rd><imm5>`，`imm5` 里 MSP=`0x08`、PSP=`0x09`，两者只差 bit0。

更值得记的一件事：**`mrseq` 和 `mrsne` 的字节完全相同**。`probe.sh` 编了一张编码矩阵，每一对 eq/ne 槽机身一字不差：

```text
     6:	f3ef 8008 	mrseq	r0, MSP        a:	f3ef 8008 	mrsne	r0, MSP
    16:	f3ef 8108 	mrseq	r1, MSP       1a:	f3ef 8108 	mrsne	r1, MSP
    26:	f3ef 8c08 	mrseq	ip, MSP       2a:	f3ef 8c08 	mrsne	ip, MSP
    36:	f3ef 8009 	mrseq	r0, PSP       3a:	f3ef 8009 	mrsne	r0, PSP
    46:	f3ef 8000 	mrseq	r0, CPSR      4a:	f3ef 8000 	mrsne	r0, CPSR
```

条件根本不在 `mrs` 里，它只存在于 `ite` 那一个词 `bf0c` 里（前一条 `tst` 决定了它_eq 还是_ne，见第四节 bit2）。顺带把 `Rd` 的位置也钉死了：`r0`/`r1`/`ip` 分别给出 `8008`/`8108`/`8c08`，`Rd` 就在 bits[11:8]。

于是"写错 Handler"有三种姿势，工具链只拦得住其中两种（`probe.sh` 把 GAS 的报错原文整段抄了下来）：

```text
  [bad_cond 拒绝] Error: incorrect condition in IT block -- `mrseq r0,psp'
  [bad_noite 拒绝] Error: thumb conditional instruction should be in IT block -- `mrsne r0,psp'
```

第三种它照收不误：把 eq 槽写成 `psp`、ne 槽写成 `msp`：

```text
00000000 <bad_slot>:
   0:	f01e 0f04 	tst.w	lr, #4
   4:	bf0c      	ite	eq
   6:	f3ef 8009 	mrseq	r0, PSP
   a:	f3ef 8008 	mrsne	r0, MSP
   e:	4770      	bx	lr
```

条件后缀跟 IT 块匹配，语法完全合法，GAS 一声不吭——但**语义整个反了**：主循环崩的时候读 PSP，任务崩的时候读 MSP，两种情况都拿到错的栈帧。真正咬人的从来不是工具链拦得住的那两种。

## 六、addr2line 反查：从栈里的 PC 到源码行

拿到 `g_frame_pc` 之后，剩下的问题就是"这个地址对应哪一行"。`fault_ctx.c` 里预备了三具"尸体"（只编译、不运行），probe 用它们把整条链路走通：

```text
080000c4 T crash_divzero
08000084 T crash_null
080000a4 T crash_unaligned
08000070 T HardFault_Handler
08000000 T hardfault_report
```

**这里有一个必须讲清的细节**：`nm` 给的 `crash_null = 0x08000084` 是**函数入口**，而栈里躺的是**出故障那一条指令**的地址。两者指的往往不是同一行：

```text
crash_null 入口    = 0x08000084（nm 给的，指向函数第一行）
crash_null
D:\Users\mcu\code\stm32\16-debug-hardfault/fault_ctx.c:69
crash_null 的 str  = 0x800008e（反汇编找的，HardFault 时栈帧里躺的就是它）
crash_null
D:\Users\mcu\code\stm32\16-debug-hardfault/fault_ctx.c:70
```

同一次崩溃，两个地址差 10 个字节，行号差 1 行：`:69` 是函数体开头（`{`），`:70` 才是那行真正的空指针写。**要拿到真凶行，就得从反汇编里找出那条出错的指令地址**，而不是拿 `nm` 的入口地址去凑。

反汇编里那条 `str` 就是凶手。`probe.sh` 第 3 段现在把 `crash_null` / `crash_unaligned` / `crash_divzero` / `fault_demo_entry` 四具机身整段打出来，本机实跑的第一具：

```text
08000084 <crash_null>:
 8000084:	b480      	push	{r7}
 8000086:	af00      	add	r7, sp, #0
 8000088:	4b04      	ldr	r3, [pc, #16]	; (800009c <crash_null+0x18>)
 800008a:	681b      	ldr	r3, [r3, #0]
 800008c:	4a04      	ldr	r2, [pc, #16]	; (80000a0 <crash_null+0x1c>)
 800008e:	601a      	str	r2, [r3, #0]
 8000090:	bf00      	nop
 8000092:	46bd      	mov	sp, r7
 8000094:	f85d 7b04 	ldr.w	r7, [sp], #4
 8000098:	4770      	bx	lr
 800009a:	bf00      	nop
 800009c:	0801012c 	.word	0x0801012c
 80000a0:	deadbeef 	.word	0xdeadbeef
```

`r3` 从 `g_null_ptr` 载入（值为 0），`str r2, [r3, #0]` 就是往地址 0 写，**空指针写的机器码长相**。它的地址 `0x800008e` 送进 `addr2line` 得到 `fault_ctx.c:70`，与源码里那行 `*g_null_ptr = 0xDEADBEEF;` 严丝合缝。

最后用链接器 map 文件交叉验证同一个地址（三处独立来源互相印证）：

```text
                0x08000084                crash_null
```

`.text` 段落在 Flash 上（`objdump -h`）：`0 .text 0000010c 08000000 08000000`，VMA 就是 `0x08000000`，与 [B1 链接四步](../build/01-four-steps.md) 讲的 Flash 起始地址一致。所以 PC 落在 `0x0800xxxx` 时，你在看的是 Flash 里的代码地址，直接喂给 `addr2line` 就对。

> `addr2line` 能查到行号的前提是编译时带了 `-g3`。probe 里交叉编译用的是 `-O0 -g3`，**优化会重排指令，`-O2` 下行号可能对不上**。调试版本务必开 `-g3` 且优先 `-O0`。

## 七、高频死因五虎

前文是"怎么破案"，这里给"常见案由"速查表。

**1. 空指针**：`PRECISERR` + `BFARVALID`，BFAR 里是那个非法地址（接近 0）。本章的 `crash_null` 就是这桩命案。

**2. 未对齐访问**：`UNALIGNED` 位。**但这桩案子平时不报案**：Cortex-M4 对单字 `LDR`/`STR` 的未对齐访问默认是硬件兜住的，只有把 `CCR.UNALIGN_TRP`（`core_cm4.h:563`，bit3）打开，它才升格成故障。多字访问（`LDM`/`STM`、`LDRD`/`STRD`）则**永远**不许未对齐。所以这类 bug 的可怕之处不是崩溃，而是**不崩**：硬件帮你偷偷做完了，你以为没事。

**3. 除零**：`DIVBYZERO` 位。同样有开关：`CCR.DIV_0_TRP`（`core_cm4.h:560`，bit4）。开关不开时 `SDIV` 只是**返回 0**，一声不吭地给你个错答案（probe 的反汇编里那条 `sdiv r3, r2, r3` 就是这个场景）。

> 所以本章的 `crash_unaligned` / `crash_divzero` 两具"尸体"，光把代码放那儿是死不了的。`fault_demo_entry` 第一句就是开这两个开关（`*(volatile uint32_t *)0xE000ED14UL |= (1<<3)|(1<<4);`，即 `SCB->CCR`，地址见 `core_cm4.h:452` 的偏移 `0x014`），反汇编里对应 `orr.w r3, r3, #24`（24 = 0x18 = bit3|bit4 的常量折叠）。你自己上板复现时，也别忘了先开。
>
> 两个 CCR 开关的复位默认值以 ARM PM0214 为准；本地未存该文档 PDF，**待回填核对**。

上面这几句不是转述二手结论。`probe.sh` 第 3 段现在把四具机身整段打出来，并对机身本身下断言，以下全是本机实跑输出：

```text
  [中] fault_demo_entry：orr[^[:space:]]*[[:space:]]+r3,[[:space:]]+r3,[[:space:]]+#24$
  [中] fault_demo_entry：0xe000ed14
  [中] crash_null：str[[:space:]]
  [中] crash_divzero：sdiv
  [中] crash_divzero：[[:space:]](bl|b\.[a-z]+|udf|bkpt|svc)[[:space:]]   （期望命中=0）
  [中] crash_unaligned：literal pool 里存在奇地址 0x08010131
```

拆开看这三具尸体的死法凭什么成立：

```text
080000a4 <crash_unaligned>:            080000c4 <crash_divzero>:
 80000ac:	607b      	str	r3, [r7, #4]     80000d0:	68fb      	ldr	r3, [r7, #12]
 80000ae:	687b      	ldr	r3, [r7, #4]     80000d2:	687a      	ldr	r2, [r7, #4]
 80000b0:	2201      	movs	r2, #1         80000d4:	fb92 f3f3 	sdiv	r3, r2, r3
 80000b2:	601a      	str	r2, [r3, #0]
 ...                                    （机身再无 bl / b.xx / udf / bkpt / svc）
 80000c0:	08010131 	.word	0x08010131
```

- **开关确实被拧开了**：入口第一条写操作就是 `orr.w r3, r3, #24`，而 `r3` 的来源是字面量池里那个 `0xe000ed14`，`SCB->CCR` 无误。
- **未对齐那具是真的未对齐**：`str` 的目标地址来自 literal pool 里的 `0x08010131`，**奇地址**，而指令本身只是最普通的 `601a str r2, [r3, #0]`。所以它死不死完全取决于那个 trap 位，不取决于代码长相。
- **除零那具没有任何陷阱**：`sdiv` 前后没有 `bl`、没有分支、没有 `udf`/`bkpt`/`svc`（这条是反向断言：命中数必须为 0）。硬件不拦它，它就老老实实返回 0。

这两条合起来说明一件事：**这两类 bug 在默认配置下根本不表现为崩溃**，它们只是悄悄给你一个错答案。想复现，先开开关；想防住，别指望它会自己炸。

**4. 爆栈**：栈溢出到非法区域时，往往在"入栈/出栈"阶段就出错，看 `MSTKERR` / `MUNSTKERR`（存储管理）或 `STKERR` / `UNSTKERR`（总线）。**这是最有诊断价值的一类**：报错位直接告诉你"是在压栈还是弹栈时死的"，一眼就能想到栈深问题。

**5. 优先级配置错误**：`PendSV` / `SysTick` 用了 [S4](04-nvic-exti.md) 讲的优先级规则，配错时表现为"中断里又触发中断"或"中断永不返回"。这类通常不产生 CFSR 位，而是**卡死在某个 handler 里**，得靠栈帧的 LR/PC 还原调用链。

## 附录：工程完整源码

**probe.c**（411 行：SCB 版图 / CFSR·SHCSR·HFSR 三张位表 / 解码器 / EXC_RETURN 判栈 / 向量槽 / 栈帧版图 / 全链路演示）：

<<< ../../code/stm32/16-debug-hardfault/probe.c

**fault_ctx.c**（103 行：naked `HardFault_Handler` + C 侧报告 + 三具只编译不运行的"尸体"，外加 `fault_demo_entry` 里开 CCR 两个 trap 位）：

<<< ../../code/stm32/16-debug-hardfault/fault_ctx.c

**probe.sh**（宿主断言 + 位号对账 + 反汇编与 addr2line 全链路 + 机身断言 + 条件指令字节学）：

<<< ../../code/stm32/16-debug-hardfault/probe.sh

## 记忆锚点

::: tip 一句话记住
**先看 CFSR 定罪名，再查 BFAR 指现场，栈里挖 PC 对行号；死因五虎：空针、错位、除零、爆栈、优先级。**
:::

**延伸**：栈帧挖 PC 依赖调用约定（[C6](../c/06-abi-stack.md)）；HardFault 与 RTOS 下看门狗超时（[S17](17-watchdog-reset.md)、[P13](../esp32/13-watchdog-health.md)）常伴生。

## 实物实验

- 三大命案各复现一次：空指针写（`*(volatile uint32_t*)0 = 0;`）、未对齐访问（奇地址强转 `uint32_t*`，记得先开 `CCR.UNALIGN_TRP`）、`x/0`。每次记录 CFSR 值与 `addr2line` 出来的行号，贴进实验记录。
- 故意把 `HardFault_Handler` 里的 `mrsne r0, psp` 改成 `mrsne r0, msp`，**注意别写成 `mrseq r0, psp`，那样根本编不过**（GAS 直接 `Error: incorrect condition in IT block`，见第五节）。改完之后机身只变一个字节（`0x09`→`0x08`），烧进板子，在 RTOS 任务里触发一次故障，感受"拿错栈指针"之后 `g_frame_pc` 读出来的垃圾数据长什么样。
- 再来一次更狠的：把 eq/ne 两槽的 `msp`/`psp` 对调。这个工具链不报错，但语义整个反了：裸机崩溃读 PSP、任务崩溃读 MSP。
- 在有 RTOS 的工程里（[F 篇](../rtos/index.md)）触发一次任务内的故障，确认 `EXC_RETURN` 的 bit2 确实是 1。

## 常见坑

- **Handler 里用 `printf` 本身再崩**：故障里跑复杂库函数可能二次故障，Handler 保持极简（直接写寄存器串口或半主机），或者像本章一样只存全局变量等 GDB。
- **MSP / PSP 拿错**：RTOS 下任务用 PSP，拿 MSP 读栈全是错的（判据是 `EXC_RETURN` 的 bit2，见第四节）。
- **没开 `-g3`**：`addr2line` 查不到行号，只会回 `??:0`，调试版本务必 `-g3`，并优先 `-O0`。
- **拿 `nm` 的函数入口地址当案发 PC**：入口地址指向函数第一行，真凶是反汇编里那条出错指令的地址，两者常常差好几天行（本章实测差 1 行、10 字节）。
- **只看 PC 不看 LR**：LR（压栈值）告诉你"从谁调用来"，调用链还原靠它，配合 map 文件追 caller。
- **以为工具链会拦住 Handler 笔误**：GAS 只校验条件后缀跟 IT 块匹不匹配，**不校验语义**。`mrseq r0, psp`（后缀错位）它拒；`mrsne r0, msp`（少一个位，RTOS 下永远读 MSP）它照收。这种地方只能靠反汇编自己核。

## 短自测

**1. 为什么 `IRQn_Type` 里没有 `HardFault_IRQn`？**

<details>
<summary>看答案</summary>

因为 HardFault 的优先级是固定的、不可设。CMSIS 的 `NVIC_SetPriority()` 只接受 `IRQn_Type`，省略该枚举等于从类型层面禁止你设优先级。`stm32f407xx.h` 第 68 行 `NonMaskableInt_IRQn = -14` 直接跳到第 69 行 `MemoryManagement_IRQn = -12`，中间的 `-13`（异常号 3）被整个略过。

</details>

**2. CFSR 显示 `PRECISERR`，但 `BFARVALID` 是 0，BFAR 里的地址能信吗？**

<details>
<summary>看答案</summary>

不能。`BFARVALID`(bit15) 是 BFAR 的"有效性位"，它为 0 时 BFAR 里是**上次残留的旧值**。同理 `MMARVALID`(bit7) 管 MMFAR。另外 `IMPRECISERR`（不精确总线错）情况下地址本身就不可靠，总线写是缓冲的，出错时 PC 可能已经跑远。

</details>

**3. 硬件压栈的 8 个字里，案发 PC 在哪个偏移？**

<details>
<summary>看答案</summary>

偏移 **24**。完整版图：0/4/8/12 = r0-r3，16 = r12，20 = LR，24 = PC，28 = xPSR，共 32 字节。写 Handler 时用 `frame[6]` 取 PC、`frame[5]` 取 LR。

</details>

**4. `crash_null` 的 `nm` 入口是 `0x08000084`，为什么 `addr2line` 要喂 `0x800008e`？**

<details>
<summary>看答案</summary>

`nm` 给的是函数入口，指向函数第一行（`:69` 的 `{`）；栈帧里的 PC 是**实际出错的那条指令**（`:70` 的空指针写）。`0x800008e` 是从反汇编里找出来的那条 `str r2, [r3, #0]` 的地址。差 10 个字节就是差一行，定位到正确行号才对得上源码。

</details>

**5. 除零为什么常常"不崩"？**

<details>
<summary>看答案</summary>

因为 `CFSR.DIVBYZERO` 的触发要先打开 `CCR.DIV_0_TRP`（`core_cm4.h:560`，bit4）。开关关着时 `SDIV` 只返回 0，不产生故障，程序继续跑，只是结果悄悄错了。未对齐访问同理（开关是 `CCR.UNALIGN_TRP`，bit3）。**这两类"不崩的 bug"比崩溃难查得多。**

</details>

**6. `mrseq r0, MSP` 和 `mrsne r0, MSP` 的机器码有区别吗？条件存在哪里？**

<details>
<summary>看答案</summary>

**没有区别**，两条都是 `f3ef 8008`（本机编码矩阵实测，eq 槽与 ne 槽机身一字不差）。MRS 的编码是 `f3ef 8<Rd><imm5>`，`imm5` 只选源寄存器：MSP=`0x08`、PSP=`0x09`、APSR/CPSR=`0x00`；`Rd` 在 bits[11:8]。**条件只存在于前一条 `ite` 的那个词 `bf0c` 里**，不带后缀的 `mrs` 本身压根没有条件域。这也解释了为什么把 `psp` 写成 `msp` 只改一个位（`imm5` 的 bit0），GAS 还不报错：它看的是后缀与 IT 块匹不匹配，那一位它不管。

</details>

## 对照表：本章概念 → 仓库落点

| 概念 | 仓库落点 |
|---|---|
| SCB 版图与六个故障寄存器地址 | `code/stm32/16-debug-hardfault/probe.c` 41–68 行 |
| CFSR 19 位表（MMFSR 6 + BFSR 7 + UFSR 6） | 同上 71–103 行 |
| SHCSR 14 位表（三个 ENA 位在 16/17/18） | 同上 104–120 行 |
| HFSR 3 位表（`FORCED` = 30） | 同上 121–126 行 |
| 位号与 CMSIS 头文件逐条对账（39 条） | `probe.sh` 第 2 段（`--dump-positions` + awk diff） |
| 解码器：位 → 死因名字 | `probe.c` 172–227 行 |
| `EXC_RETURN` 判栈（bit2）与 FPU（bit4） | 同上 248–280 行（`exc_return_uses_psp` / `has_fpu`） |
| 向量槽 = `IRQn + 16` | 同上 281–310 行 |
| 栈帧版图（PC 在偏移 24） | 同上 311–335 行；`fault_ctx.c` 22–24 行 |
| naked `HardFault_Handler` 汇编 | `fault_ctx.c` 50–61 行 |
| C 侧报告（读 SCB + 抄栈帧） | 同上 27–48 行 |
| 三具"尸体"（空指针 / 未对齐 / 除零） | 同上 65–86 行 |
| `addr2line` 全链路与 map 交叉验证 | `probe.sh` 第 3 段 |
| 四具机身打印 + 机身断言（五虎里两具"死不了的尸体"） | `probe.sh` 第 3 段末（`SEC` / `chk` / 奇地址 literal pool） |
| 条件指令的字节学：`ite` 带条件、MRS 编码矩阵、GAS 拒绝原文 | `probe.sh` 第 4 段（`enc_*.s` / `mrs_matrix.s` / `bad_*.s` + `cmp -l`） |

## 你做到了

- HardFault 从"玄学死机"变成"按流程破的案"；
- 你手上有了三份验尸报告 + 一条 PC → 行号的全链路；
- S 篇收官：你已有能力独立调试任何裸机疑难。

<div class="achievement">
✅ S 篇收官。下一站：<a href="../rtos/index.html">RTOS 篇</a>：从"一个超级循环"到"多个平行世界"，先看 FreeRTOS 怎么变魔术。
</div>

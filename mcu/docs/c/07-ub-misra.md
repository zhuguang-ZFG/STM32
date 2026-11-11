---
title: C7 未定义行为与 MISRA-C 精要
status: done
difficulty: 3
minutes: 35
---

# C7 未定义行为：那些"能跑但会炸"的写法

> 🎯 UB（未定义行为）最阴险的地方：代码**看起来对、编译通过、今天能跑**——直到换编译器版本、换优化等级、或者客户演示那天，它才炸给你看。嵌入式没有操作系统替你挡枪，UB 就是定时炸弹。

## 本章精髓

1. UB ≠ 报错：标准甩手不管，编译器就可以**以"你没有 UB"为前提做优化**：`x+1 > x`（有符号溢出）能被优化成恒真。
2. 高危三兄弟：有符号溢出、移位越界（`1<<33`）、严格别名冲突（用不兼容类型的指针访问同一对象）。
3. MISRA-C 不是繁文缛节：它把"炸弹区"画成红线，汽车/医疗固件靠它活命；我们取其中性价比最高的 10 条自用。

- **能理解**：拿 probe 工程的**真跑输出**逐条对账：`is_bigger_after_inc(INT_MAX)` 在 -O0/-O2/-fwrapv 三档下的读数、`1u<<33` 在两档下的变脸、ARM 汇编里 `movs r0, #1` 那两行铁证，以及宿主 x86 上 `-O0` 函数体就已经是 `movl $1, %eax`、`-O2` 连 `call` 都不剩的那两段。
- **能用**：给一段新代码，先扫三兄弟；给一次"昨天还好好的"灵异故障，第一反应查优化等级差异，而不是怀疑硬件。

## 先修

- [C2 指针](02-pointer.md)、[C3 volatile](03-volatile.md)、[C4 结构体与 ABI](04-struct-abi.md)。

## 先跑起来（10 分钟 quick win）

```bash
cd code/c/07-ub-misra
sh probe.sh   # 宿主 gcc 真跑三档对照 + 编译器防线现场 + ARM 交叉汇编铁证
```

跑之前先押：第一个对照实验里的边界比较，在两个优化档位下各返回几？十年前的老教程有标准答案，它今天还作数吗？两注都下完，再看读数。

先看两个读数（gcc 16.1.0 实测）：

- `is_bigger_after_inc(INT_MAX) = 1`：**两个优化档位都返回 1**。十年前的老教程说"-O0 返回 0、-O2 返回 1"，在 gcc 16 上前半句已经翻案：折叠器在 -O0 也工作。亲眼看到优化器"利用"UB 之后，本章后面每句话你都会读得很认真。
- `shift_oob(1u, 33u)`：**-O0 是 2，-O2 是 0**：真正当场变脸的是移位。同一行代码，两档答案，哪个都不算"错"，因为 UB 没有标准答案。

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| UB 的优化逻辑 | 编译器为什么"有权使坏"；INT_MAX 案例全程复盘 | 代码分析 |
| 移位雷区 | `1<<33`、负数移位、移位超过位宽；寄存器掩码的安全写法 | 代码分析 |
| 严格别名 | float 与 uint32 互看的正确姿势（memcpy/union 之争） | 代码分析 |
| MISRA 十条 | 精选取舍：类型转换、运算符优先级括号化、禁递归等 | 配置 |
| 检查工具链 | -Wall -Wextra -Wconversion -fstack-usage；静态分析简介 | 库解析 |

## 动画：编译器如何利用 UB 做优化

源代码 → 编译器推理（"你保证没有 UB"）→ 汇编折叠为常量 → 运行时行为与数学期望偏离。盯住"编译器假设"那一步，它是整个优化链的起点。

![UB 编译器优化陷阱](/anim/ub-compiler-trap.svg)

## 一、UB 的优化逻辑：编译器凭什么"使坏"

C 标准把程序行为分成三类：**定义良好的**、**实现定义的**（编译器得选一个并写进文档）、**未指定的**（随便哪个都行但不许炸）。UB 是第四类：**标准直接撒手**：行为可以是任何东西，包括"看起来正常工作"。这不是标准的疏忽，是刻意的交易：把某些情形划成"不许发生"，编译器才能拿着这条禁令当优化燃料。

`is_bigger_after_inc`（probe.c 第 26 行）就是教科书案例：

```c
int is_bigger_after_inc(int x) { return x + 1 > x; }   // 有符号溢出：x=INT_MAX 时 UB
```

数学上 `x+1 > x` 只有在 `x = INT_MAX` 时为假，而那一刻 `x+1` 已经溢出，是 UB。编译器的推理链很短：**你保证不喂我 INT_MAX，那这个比较永远为真，函数可以整段折叠成 `return 1`。** ARM 交叉汇编（arm-none-eabi-gcc 15.2.1，`-mcpu=cortex-m4 -O2`，probe.sh 第 5 步取证）：

```asm
is_bigger_after_inc:
	movs	r0, #1        @ 整个函数只剩"装载常量 1"
	bx	lr
```

两行。没有加法、没有比较，它们被"你不会溢出"这条假设吃掉了。对照 `-fwrapv -O2`：这个编译旗把有符号溢出**重新定义**为按补码回绕，编译器失去"假设权"，只能真算：

```asm
is_bigger_after_inc:
	mvn	r3, #-2147483648   @ r3 = ~0x80000000 = 0x7FFFFFFF（INT_MAX）
	subs	r0, r0, r3          @ x - INT_MAX：x==INT_MAX 时 Z 置位
	it	ne
	movne	r0, #1              @ x ≠ INT_MAX → 1；x == INT_MAX → 0
	bx	lr
```

gcc 的推理：既然回绕定义下 `x+1 > x` 等价于"x 不等于 INT_MAX"，那就用一次减法+条件置位实现。

> 换一把编译器，这段的形状会变、结论不变。本机另一把 arm-none-eabi-gcc 10.3.1（PATH 里默认那把）给的是 `adds r3, r0, #1` / `cmp r3, r0` / `ite le` / `movle r0, #0` / `movgt r0, #1`，老老实实加一次、比一次。**两把编译器只是"真算"的方式不同，都不肯把函数折成常量**，这才是 `-fwrapv` 要证明的事。这也是本章反复强调的一条纪律：引用汇编必须注明工具链版本，`probe.sh` 第 5 步之所以先把版本号打出来。

宿主实测三档读数（gcc 16.1.0）：

| 编译档 | `is_bigger_after_inc(INT_MAX)` | 解释 |
|---|---|---|
| `-O0` | **1** | 老梗"-O0 返回 0"已在 gcc 16 翻案：折叠在 -O0 也发生 |
| `-O2` | **1** | 恒真折叠，两行汇编 |
| `-O2 -fwrapv` | **0** | 溢出被定义为回绕 → INT_MAX+1 = INT_MIN，比较为假 |

这张表比任何说教都狠：**同一个二进制符号，三种编译配置，两种答案**。"昨天还好好的"这种灵异故事，第一嫌疑人从来不是硬件，是优化等级。

"-O0 也折叠"不是嘴上说说，把宿主汇编拉出来（probe.sh 第 6 步，gcc 16.1.0 x86-64）：

```asm
is_bigger_after_inc:              @ -O0
	pushq	%rbp
	movq	%rsp, %rbp
	movl	%ecx, 16(%rbp)
	movl	$1, %eax               ← 加法、比较都不在，只剩装载常量
	popq	%rbp
	ret
```

`-O0` 的 `main` 仍然规规矩矩 `call is_bigger_after_inc`，可函数体里已经没人算账了。`-O2` 更狠：`main` 里 `is_bigger_after_inc` / `shift_oob` / 两种位读法**四个 call 全消失**，喂给 printf 的直接是立即数：

```asm
	movl	$1, %edx               @ is_bigger_after_inc(INT_MAX) → 恒真折叠
	xorl	%edx, %edx             @ shift_oob(1u, 33u) → 0（UB 之后编译器爱给什么给什么）
	movl	$1065353216, %edx      @ bits_union(1.0f)   → 0x3F800000
	movl	$1065353216, %edx      @ bits_memcpy(1.0f)  → 同一个立即数
```

而 `-O0` 的 `shift_oob` 函数体里，躺着一条真真切切的 `sall %cl, %edx`，计数 33 被移位器截成 1，所以读数是 2。**结论：`-O0` 不等于"逐行照实执行"，它只是不在调用点做折叠、不在函数间做传播；同一个函数体内的模式匹配，gcc 16 在 `-O0` 照做。** 这就是"我 -O0 跑过了"永远不能当正确性证据的原因。

一个容易搞反的推论：UB 最可怕的形态不是崩溃，是**悄悄改变逻辑**。`movs r0, #1` 让程序"正常跑着"，只是从此这个函数对 INT_MAX 撒谎，而你可能在它上面盖了三层缓存逻辑。回到 [C3 volatile](03-volatile.md) 的主题：编译器不是"老实人"，它是"规则怪兽"：规则内它可以把你的代码改得亲妈都不认识，规则外（UB）它连改都不用跟你商量。

**UB 的另一面是 HardFault**：数组越界、空指针解引用、未对齐访问，这些 UB 在 ARM 上会直接触发 [S16 HardFault](../stm32/16-debug-hardfault.md)。用 `-fsanitize=undefined`（主机侧）或 `-fstack-protector`（嵌入式侧）提前抓人，比等 HardFault 再查效率高十倍。

## 二、移位雷区：最便宜也最频繁的一刀

移位是嵌入式使用频率最高的运算（每一个寄存器掩码都是它），也是 UB 密度最高的运算。C 标准划了三条红线：

1. **移位计数 ≥ 操作数位宽**：UB，与操作数有无符号**无关**：`1u << 33` 同样炸；
2. **移位计数为负**：UB；
3. **左移把 1 移进/移出有符号数的符号位**：UB（如 `(int)1 << 31`）。

probe.c 第 29 行把计数走运行期变量（编译期拦不住），实测 `1u << 33`：

```text
----- -O0 -----          shift_oob(1u, 33u) = 2
----- -O2 -----          shift_oob(1u, 33u) = 0
```

-O0 为什么是 2？因为真机指令就在那儿跑：x86 的 `shl` 与 Cortex-M 的 `lsl` 都把计数截到操作数位宽的低 5 位（32 位操作数 → 计数 & 31），`33 & 31 = 1`，于是 `1u << 1 = 2`。-O2 为什么是 0？编译器认出 UB 后，结果可以"任意"，它选了个最省指令的答案。**两个答案都不是"错"，因为 UB 题目本身没有标准答案。**

这就是 [C6 栈帧实验](06-abi-stack.md)里 BSRR 掩码写成 `1UL << (LED_R_PIN+16)` 的原因，三条纪律层层设防：

- **字面量类型先行**：`1` 是 int（32 位有符号），`1 << 31` 踩红线 3，`1 << 33` 踩红线 1；写 `1UL`（64 位宿主上仍是 32 位无符号字面量，但无符号左移不存在符号位问题）只防住红线 3，**防不住红线 1**。
- **计数必须可证 < 位宽**：`LED_R_PIN` 是枚举常量（编译期可见），`+16` 后是 22/23/24 < 32，两条红线都躲开。若计数来自运行期数据（协议字节、寄存器值），先检查再移：

```c
if (n < 32u) {
    mask = 1u << n;          /* 计数已证 < 位宽：安全 */
} else {
    return false;            /* 拒绝，别让硬件替你决定 */
}
```

- **负数禁止入场**：`int8_t` 的计数先转 `unsigned` 再检查范围，有符号计数在"检查前"就已经踩了红线 2。

顺带一句 `-fwrapv` 的边界（实测）：它只救有符号加/减/乘的溢出，**移位三条红线一条都不救**（probe 第 2 步：`-fwrapv -O2` 下 `1u<<33` 依旧是 0）。别指望一个编译旗包打天下。

## 三、严格别名：float 与 uint32 互看的正确姿势

![严格别名：指针强转是 UB，union/memcpy 才是合法写法](/figures/c-07-strict-alias.svg)

C 规定：访问对象必须用**兼容类型**的左值表达式，少数例外（`char*` 谁都能指、加过限定符的同类型、union 自己的成员）。拿 `uint32_t*` 去解引用一个 float 对象，就是"严格别名违规"，UB 三兄弟里最隐蔽的一个，因为**它十年都不一定发作**。

编译器为什么在意：别名分析是优化的地基。如果编译器敢假设"这个 uint32_t 写入不会改到那个 float"，它就能把两次 float 读合并成一次、把 store 重排到 load 前面。你的违规代码就是在这条假设上打洞。抓捕现场（probe.sh 第 3 步，alias-violate.c 第 13 行）：

```text
warning: dereferencing type-punned pointer will break strict-aliasing rules [-Wstrict-aliasing]
   13 |     return *(uint32_t *)&f;
```

两种**合法**写法（probe.c 第 32–44 行，实测输出）：

```c
/* 读法一：union 双关——C11 起脚注给了正式说法（写一个成员、读另一个是"指定位模式重解释"） */
static uint32_t bits_union(float f)
{
    union { float f; uint32_t u; } pun;
    pun.u = 0u;
    pun.f = f;
    return pun.u;
}

/* 读法二：memcpy——标准层面永远合法，编译器会把它优化成一条 load */
static uint32_t bits_memcpy(float f)
{
    uint32_t u;
    memcpy(&u, &f, sizeof u);
    return u;
}
```

```text
bits_union(1.0f)   = 0x3F800000
bits_memcpy(1.0f)  = 0x3F800000
```

两种读法位级一致（断言 2/2 之一）。选型建议很朴素：

- **跨类型取位**（float→位串、CRC 算法吃结构体字节）：**memcpy**：零心智负担，"看似函数调用"会被优化器消掉，生成的就是一条访存指令；
- **既取位又想省一次拷贝**：union 双关：嵌入式老代码的传统写法，C11 已转正，但记得 [C4](04-struct-abi.md) 的提醒：它依赖"同存储、同对齐"这一层实现约定，跨平台代码仍以 memcpy 为锚；
- **字节序敏感**（网络协议、EEPROM 布局）：走 `unsigned char*` 逐字节拼（alias-violate.c 第 18 行的对比组），char 是别名规则的天生例外，且逐字节代码读得出字节序。

什么情况**不需要**双关：调 [S9 ADC](../stm32/09-adc.md) 时把半字数据当 int 看，那不叫别名违规，叫"本来就该用正确的类型读正确的地址"。别名规则管的是**同一块存储的两种身份**，不是"我 cast 了一个外设寄存器指针"。外设寄存器访问走 volatile 指针（回 [C3](03-volatile.md)），那是另一个学科。

## 四、嵌入式 MISRA 十条：自选的"红线地图"

MISRA-C:2012 全本 300+ 条，汽车/医疗行业全量合规。取信条的思路是：把历史上**真实炸过**的 UB 高发区画成红线，剩下的按团队成本自选。我们的自选十条（编号给到 MISRA-C:2012 中有明确对应、且值得背号的）：

1. **声明即初始化**（Rule 8.9 的精神 + -Wuninitialized 抓现行）：`int x;` 后面读 = UB；写代码时变量定义挪到能初始化的位置。
2. **隐式转换显式化**（Rule 10.x 类型模型）：`uint16_t` 与 `int` 混算、有符号无符号比较，一律显式 cast 或统一类型，[C4](04-struct-abi.md) 的整型提升坑在这条线上。
3. **移位计数先验证**：上节的三条红线；掩码宏的参数必须"编译期可证 < 位宽"或运行期先查。
4. **位运算与比较不裸混**：`flags & MASK == MASK` 解析成 `flags & (MASK==MASK)`，`==` 优先级高于 `&`，加括号不丢人（Rule 12.x 的精神）。
5. **禁递归**（Rule 17.2）：裸机栈按 [C6](06-abi-stack.md) 算过账：每层一帧，没有哨兵，爆栈不报错。树形逻辑用显式栈迭代。
6. **指针运算只在数组圈内**（Rule 18.1 的精神）：指向"尾后一"可以、解引用"尾后一"是 UB；跨对象做指针差是 UB。
7. **禁 goto 直穿初始化**：向上 goto 跳过变量初始化 = 读未初始化 = UB；错误处理出口统一（单出口风格），跳转只向下。
8. **switch 必有 default**（Rule 16.x 的精神）：枚举 switch 加齐 default 并 abort/log，新增枚举值时固件"炸得响"比"悄悄漏"好。
9. **volatile 纪律**：外设寄存器、ISR 与主循环共享的变量一律 volatile（[C3](03-volatile.md) 全章）；但 volatile 不解决原子性，那是 [S4 NVIC](../stm32/04-nvic-exti.md) 的活。
10. **无副作用依赖**：`&&`/`||` 右侧、`if` 条件、`sizeof` 里的表达式，其副作用不许是程序依赖的一部分：表达式既要求值又要求副作用，重排/短路就会改变行为。

十条的共同句式：**把"编译器可以任意解释"的地带，用写法约束收窄成"只有一种读法"**。这正是 MISRA 的哲学：语言的自由度是给写编译器的人的，不是给写固件的人的。

## 五、检查工具链：三道防线自动化

第一道防线是**编译警告**，零成本、可自动执行。抓捕现场（probe.sh 第 3 步真实输出）：

```text
oob-static.c:19:14: warning: 'x' is used uninitialized [-Wuninitialized]
oob-static.c:12:10: warning: array subscript 7 is above array bounds of 'int[4]' [-Warray-bounds=]
alias-violate.c:13:13: warning: dereferencing type-punned pointer will break strict-aliasing rules [-Wstrict-aliasing]
```

三个 UB 三兄弟的"编内成员"，三个警告各就各位。军备建议按档加：

- **起步价**：`-Wall -Wextra`，配 `-Werror` 让 CI 拦人（本站所有工程的标准旗）；
- **加一档**：`-Wconversion -Wsign-conversion`：隐式收窄/符号转换全部点名，前三章所有坑这条旗都能提前吹哨；
- **专项**：`-Wstrict-aliasing`（别名）、`-Warray-bounds`（越界）、`-Wuninitialized`（未初始化）、`-fstack-usage`（每函数栈账单：[C6](06-abi-stack.md) 的栈预算从猜测变核对，喂给 [B5 map 与体积](../build/05-map-size.md) 的体积审计）。

第二道防线是**运行期仪表**：`-fsanitize=undefined`（UBSan）在真机上给 UB 点名。诚实记录：本站宿主工具链（MinGW-Builds gcc 16.1.0）没有带 UBSan 运行库，probe.sh 第 4 步自动跳过（"编译期防线不受影响"）；有 Linux 环境时同一段 ub.c 会打出 `runtime error: signed integer overflow`。交叉链上 UBSan 支持有限，所以嵌入式的主战场是第一、三道防线。

第三道防线是**静态分析**：cppcheck（免费、快、对 MISRA 子集有专用检查）、clang-tidy、gcc 自带 `-fanalyzer`。它们与 -Wall 的分工：-Wall 看"这一行"，静态分析看"这条数据流"：未初始化的传播链、空指针的所有分支路径。

三道防线的成本-收益排序很清晰：警告 0 成本、CI 0 成本、静态分析一杯咖啡、UBSan 一台 Linux。**先让前两道变成默认**，你的 UB 故事会少 90%。

## 附录：工程完整源码

本章取证工程 `code/c/07-ub-misra/`（`sh probe.sh` 一条命令跑完，不需要开发板）：

**probe.c**（运行期取证：溢出/移位/两种合法位读法）：

<<< ../../code/c/07-ub-misra/probe.c

**alias-violate.c / oob-static.c**（专供编译器警告抓人的违规现场）：

<<< ../../code/c/07-ub-misra/alias-violate.c

<<< ../../code/c/07-ub-misra/oob-static.c

**ub.c**（UBSan 点名用例，工具链支持时启用）：

<<< ../../code/c/07-ub-misra/ub.c

**probe.sh**（三档对照 + 防线现场 + ARM 交叉汇编取证）：

<<< ../../code/c/07-ub-misra/probe.sh

## 记忆锚点

::: tip 一句话记住
**UB 三兄弟：溢出、移位、别名，今天跑通不等于明天安全；加括号不丢人，显式转换不寒碜。**
:::

## 实物实验

- 把 00-blink 的 `1UL << (LED_R_PIN+16)` 故意写成 `1 << (LED_R_PIN+16)` 再改成 `1 << 33` 对比反汇编，体会"1 的类型和移位数"为什么是掩码代码的生命线（我们的写法用 `1UL`）。
- 进阶：把 `-O0` 与 `-O2` 两版固件都烧进板子，看移位越界版本在两种固件里**行为不一致**，板子会诚实地告诉你 `-fstack-usage` 之外，优化等级也是一种"硬件配置"。

## 常见坑

- **以为警告=错误**：`-Wall` 只是起步价；嵌入式建议 `-Wall -Wextra -Wconversion`，警告清零。
- **`char` 当数值用忘定符号**：`char` 默认有无符号是实现定义，寄存器/协议字节一律 `uint8_t`。
- **联合体类型双关**：C11 允许 union 读别的成员但有尾洞/表示风险；跨类型 reinterpret 首选 `memcpy`（编译器会优化成一条 load）。
- **递归**：MISRA 禁递归不是教条，裸机栈就那么点，爆栈无哨兵（回 [C6](06-abi-stack.md)）。
- **把"-O0 能跑"当"代码正确"**：gcc 16 连 -O0 都开始折叠 `x+1>x`；证明正确性的从来不是"跑起来过"，是"没有 UB + 警告清零"。

## 短自测

**1. `is_bigger_after_inc(INT_MAX)` 在本站宿主 gcc 16.1.0 的 -O0、-O2、`-O2 -fwrapv` 三档下读数各是多少？为什么前两档相同？**

<details><summary>看答案</summary>

1、1、0（probe.sh 第 1、2 步实测）。前两档相同是因为折叠 `x+1>x → 1` 的模式匹配在 -O0 也执行（gcc 16 行为，老教程"-O0 返回 0"已翻案；probe.sh 第 6 步直接把 `-O0` 的函数体拉出来，里面只剩一句 `movl $1, %eax`）；`-fwrapv` 把有符号溢出定义为回绕，编译器失去"假定不溢出"的权利，只能真算：INT_MAX+1 回绕成 INT_MIN，比较为假，读数 0。

</details>

**2. `1u << 33` 为什么在 -O0 下等于 2？-O2 下等于 0 说明什么？**

<details><summary>看答案</summary>

-O0 走真机指令：x86 `shl`/Cortex-M `lsl` 都把移位计数截到低 5 位，`33 & 31 = 1`，`1u << 1 = 2`（probe.sh 第 6 步：`-O0` 的 `shift_oob` 函数体里确实躺着一条 `sall %cl, %edx`）。-O2 等于 0 说明编译器认出了 UB（计数 ≥ 位宽，无符号也一样）并选择了"任意结果"里最省指令的那个：第 6 步里 `-O2` 的 `main` 连 `call shift_oob` 都没有了，直接 `xorl %edx, %edx` 把 0 塞给 printf。两个答案都不算错，UB 题目没有标准答案，这正是要避开它的原因。

</details>

**3. 想看 float 的位模式，写出两种合法写法并说出它们的法理依据；`*(uint32_t*)&f` 错在哪？**

<details><summary>看答案</summary>

合法一：union 双关（C11 脚注对"写一成员读另一成员"给出位模式重解释的正式说法）；合法二：`memcpy` 到 uint32_t（对象表示复制，永远合法，优化后就是一条 load）。`*(uint32_t*)&f` 用不兼容类型的左值访问 float 对象，违反严格别名规则，编译器可基于"这类访问不存在"的假设做 load 合并与 store 重排，行为无保证。

</details>

**4. `-fwrapv` 能救 `1u << 33` 吗？依据是什么？**

<details><summary>看答案</summary>

不能。`-fwrapv` 只把**有符号加/减/乘**的溢出定义为按补码回绕；移位的三条红线（计数 ≥ 位宽、计数为负、有符号左移穿符号位）一条都不在其保护范围（probe 实测：`-fwrapv -O2` 下 `1u&lt;&lt;33` 读数仍为 0）。移位安全的唯一途径是计数先验证。

</details>

**5. 背出"嵌入式 MISRA 十条"中与你最近一次 bug 最相关的一条，并说出它的 UB/缺陷机理。**

<details><summary>看答案</summary>

（开放题，示例）第 4 条"位运算与比较不裸混"：`flags & MASK == MASK` 因 `==` 优先级更高，实际解析为 `flags & (MASK == MASK)`，即 `flags & 1`，逻辑悄悄变成"最低位为 1"，编译器不警告（表达式合法），测试可能恰好全过。机理是 C 运算符优先级表把 `&` 排在 `==` 之后，与人类阅读直觉相反；红线写法就是给位运算加括号。

</details>

## 对照表：本章概念 → 仓库落点

| 概念 | 仓库落点 |
|---|---|
| 溢出折叠 `movs r0,#1` | `code/c/07-ub-misra/probe.sh` 第 5 步（build/probe-arm.s） |
| -fwrapv 真算汇编（x≠INT_MAX 变换） | probe.sh 第 5 步对照段（build/probe-arm-wrapv.s） |
| 换一把编译器的另一形状（`adds`/`cmp`/`ite`） | `XPACK=/none sh probe.sh`（退回 PATH 默认那把 10.3.1） |
| -O0 宿主函数体已折叠成 `movl $1, %eax` | probe.sh 第 6 步（build/host-o0.s） |
| -O2 `main` 四个 call 全消失、printf 吃立即数 | probe.sh 第 6 步（build/host-o2.s） |
| 三档读数表（1/1/0） | probe.sh 第 1、2 步实测输出 |
| 移位越界两档变脸（2/0） | probe.sh 第 1 步；`shift_oob` 见 probe.c 29 行 |
| 合法位读法 + 位级断言 | probe.c 32–44、59–66 行（bits_union/bits_memcpy） |
| 别名违规抓捕现场 | alias-violate.c 13 行；probe.sh 第 3 步 |
| 越界/未初始化警告现场 | oob-static.c 12、19 行；probe.sh 第 3 步 |
| UBSan 用例与跳过逻辑 | ub.c 全文；probe.sh 第 4 步 |
| 掩码纪律 `1UL << (LED_R_PIN+16)` | code/stm32/00-blink 工程与 [S3](../stm32/03-gpio.md) |

## 延伸阅读

本章只讲了嵌入式最常撞的几条；完整清单与"UB 真会咬人"的证据在这里：

- **[\[C1\]](../reference/bibliography.md#toolchain)** N1570 附录 J.2 — C11 全部未定义行为的官方清单，两百余条。
- **[\[D8\]](../reference/bibliography.md#papers)** Wang et al. 2013 — 优化器利用 UB 删掉空指针检查、溢出检查的真实案例集（Linux、PostgreSQL……）。
- **[\[C2\]](../reference/bibliography.md#toolchain)** MISRA C:2012 / C:2023 — 本章规则取舍的原文。

## 你做到了

- 拿到一张"UB 雷区地图"和一套编译器防线；
- 看老代码时眼里多了三兄弟的探测器。

回到开场那颗「客户演示那天才炸」的定时炸弹：你现在知道引信在哪了——不是硬件不稳，是编译器拿「你保证没有 UB」当优化燃料。三兄弟过一遍、防线拉起来，下次「昨天还好好的」再出灵异故障，第一嫌疑人换成优化等级，而不是示波器。

<div class="achievement">
✅ C 篇收官。下一站：<a href="../build/index.html">B 篇 构建与运行</a>：看你写的 C 如何一步步变成固件，全程开盒。
</div>

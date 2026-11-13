---
title: "volatile、const 与未定义行为"
platforms: [generic]
---

# volatile、const 与未定义行为

> 同一段轮询，`-O0` 跑得好好的，`-O2` 一开就死等。编译器没有坏，它只是不知道那个地址后面藏着一台会自己变状态的机器。

## 本章罗盘

- **问题**：同一段轮询，`-O0` 能等到标志位，`-O2` 却原地死转；`flag ^= 1` 已经标了 `volatile`，中断里的一次更新还是会丢；`x + 1 > x` 在 `x = INT_MAX` 时返回 1，`1u << 33` 在 `-O0` 与 `-O2` 下给出两个答案。三个现象分别指向优化器的授权范围、`volatile` 的合同边界和未定义行为的代价。
- **交付**：能给任意一段访存代码生成 `-O0` 与 `-O2` 两份汇编，指出哪次读被缓存、哪次写被删除、哪几次读-改-写被合并；能写对 `volatile` 与 `const` 的每个组合；能把掩码移位的计数证明到编译期或运行期；能用 `union` 或 `memcpy` 合法地看 `float` 的位模式。
- **边界**：本章以单核 Cortex-M4 裸机为主，例子来自来源记录的 x86-64 宿主与 Cortex-M4 交叉两套产物；宿主读数只用于复现，板上的真相以 M4 那份为准。F407 没有数据 cache，`volatile` 加屏障基本够用；ESP32-S3 这类带数据 cache 的核，DMA 共享缓冲还要清理与无效化。MISRA 一节是自选十条，不是全量合规。结构体布局与寄存器映射见[第 3 章](./03-struct-abi-registers.md)，工具链与优化档见[第 5 章](./05-toolchain-four-steps.md)，链接与启动见[第 6 章](./06-linker-startup-map.md)，HardFault 现场见[第 19 章](../v2-reliability/19-watchdog-reset-hardfault.md)。
- **依据锚点**：C3《volatile：跟编译器约法三章》（`mcu/docs/c/03-volatile.md`）、C7《未定义行为与 MISRA-C 精要》（`mcu/docs/c/07-ub-misra.md`）；ISO/IEC 9899:2018 §5.1.2.3（程序执行）、§6.7.3（类型限定符）与附录 J.2（未定义行为清单），均转引自上述来源；MISRA C:2012 的规则编号同样转引自 C7。变量的段归属与 `const` 的 RAM 账在[第 1 章](./01-c-memory-model.md)。

## 先做出来

这一节不需要开发板，只需要两套编译器：宿主 `gcc` 和 `arm-none-eabi-gcc`。目标是把同一份源码在 `-O0` 与 `-O2` 下各编一次，亲眼看到优化器删掉了什么。

先跑 volatile 取证工程：

```bash
cd mcu/code/c/03-volatile
gcc -std=c11 -Wall -Wextra -O2 -S -o opt_probe.O2.s opt_probe.c
arm-none-eabi-gcc -std=c11 -Wall -Wextra -mcpu=cortex-m4 -mthumb -O2 -S -o opt_probe.m4.O2.s opt_probe.c
```

跑之前先押一个数字：那个空转一千圈的延时函数，优化后会剩几条指令？然后在产物里搜 `delay_plain`：

```asm
delay_plain:              ; x86-64, -O2
    ret
```

```asm
delay_plain:              ; Cortex-M4, -O2
    bx      lr
```

一条返回，一千圈延时在产物里没有存在过。再搜 `poll_plain`：

```asm
poll_plain:               ; Cortex-M4, -O2
    ldr     r3, .L5
    ldr     r3, [r3]      ; 整个函数只读这一次
    lsls    r3, r3, #31
    bpl     .L3
    movs    r0, #42
    bx      lr
.L3:
    b       .L3           ; 死转：不再碰那块内存
```

对照 `poll_volatile`，循环回到每圈一条 `ldr r3, [r2, #4]`，读被保住了。接着跑未定义行为取证工程：

```bash
cd mcu/code/c/07-ub-misra
sh probe.sh
```

gcc 16.1.0 宿主读数：

```text
is_bigger_after_inc(INT_MAX)   -O0 → 1    -O2 → 1    -O2 -fwrapv → 0
shift_oob(1u, 33u)             -O0 → 2    -O2 → 0
```

两个读数值得停一下：`-O0` 也把 `x + 1 > x` 折成了 1，老教程说的“-O0 返回 0”在 gcc 16 上不成立；`1u << 33` 却在两档之间变了脸，因为它是 UB，没有标准答案。这两件事是本章后半程的主线。

## 机制

### as-if：优化器只对可观察行为负责

C 标准给编译器的授权写在 §5.1.2.3：只要可观察行为不变，中间的指令随它排。可观察行为包括 `volatile` 访问、文件写入、交互设备的输入输出；普通内存的读写不在其中。于是优化器做三件天经地义的事：

| 优化动作 | 对普通内存 | 对硬件寄存器 |
| --- | --- | --- |
| 缓存：多次读合成一次，值留在寄存器 | 完全正确 | 错——这几次读之间硬件自己变了 |
| 删除：写了没人再读的赋值（死 store） | 可以删 | 错——那次写本身就是目的 |
| 合并：连续两次置位写合成一次 | 等价 | 错——硬件要两个动作，你只发了一个 |

`volatile` 的语义就是把这三项授权收回：每次使用都必须真实访存，不许缓存、不许删、不许凭空造。它只管“访存”这一件事，不改值的含义，不是 `atomic`，也不是锁。另有一条常被忽略：没有副作用的空循环，编译器可以假定它会终止（C11 起不终止按未定义处理），这解释了 `delay_plain` 连缓存都没用上、整个消失。

![volatile 的访存合同：读一次 vs 每次读](/anim/volatile-as-if.svg)

### volatile 的访存合同：四个现场

取证环境是两套工具链，同日实测，均 `-std=c11 -Wall -Wextra` 零告警：宿主 MinGW-Builds gcc 16.1.0（x86_64-posix-seh）与 xPack arm-none-eabi-gcc 15.2.1（`-mcpu=cortex-m4 -mthumb`）。两边优化决策一模一样：同一个优化器、同一条 as-if 规则，只是指令形式不同。x86 那份方便在本机 30 秒复现，Cortex-M4 那份才是板子上真正会跑的东西。

#### 现场 1：轮询状态位——读一次 vs 每次读

源码只有一处差别：`unsigned int` 与 `volatile unsigned int`。`-O0` 下 `poll_plain` 每圈都真访存，这才是“-O0 能跑”的真相。`-O2` 下 x86-64 把判断依据读到寄存器一次（`testb $1, g_status(%rip)`），没置位就跳进 `.L3: jmp .L3`；M4 那份就是前面看过的 `b .L3`，一条指令的紧死循环，没有访存、没有中断以外的出口。板子看起来活着（SWD 还能连），这段代码永远不会往下走。判断依据被缓存在寄存器里，bit0 后来被硬件置 1，代码不会知道。换 `poll_volatile`，`-O2` 下循环回到每圈访存，x86 是 `testb $1, v_status(%rip)`，M4 是 `ldr r3, [r2, #4]`。

![编译器把 flag 缓存进寄存器，ISR 在内存里写 1；轮询循环因此看不到更新](/figures/c-03-volatile.svg)

#### 现场 2：软件延时——整个循环被删

`delay_plain(unsigned n) { while (n--) {} }` 的 `-O2` 产物只有一条 `ret`（x86-64）或 `bx lr`（Cortex-M4），你写的“500 ms”变成 0 ms。把参数改成 volatile，`delay_volatile` 把计数钉在内存（栈槽），每圈读写：

```asm
delay_volatile:                ; Cortex-M4, -O2
    sub     sp, sp, #8
    str     r0, [sp, #4]       ; 计数落栈槽
.L15:
    ldr     r3, [sp, #4]
    subs    r2, r3, #1
    str     r2, [sp, #4]       ; 每圈写回
    cmp     r3, #0
    bne     .L15
    add     sp, sp, #8
    bx      lr
```

延时的另一条出路是给它真实副作用：`00-blink` 在循环体里放 `__asm__ volatile ("nop")`。这个 `volatile` 是 asm 语句的限定符，与对象类型限定符是两套规则：表示这段汇编不许删、不许移动、不许合并，同时给循环注入副作用。周期数仍取决于主频与优化档，工程注释里“约 0.5 s（-O0 实测校准）”就是这个意思，换时钟源要重新校准。

#### 现场 3：配置序列被合并成一次写

三个连续 `|=` 想表达“依次置位三个使能位”。普通结构体（寄存器访问漏了 volatile）：

```asm
cfg_plain:                     ; Cortex-M4
    ldr     r3, [r0]
    orr     r3, r3, #7         ; 三次读-改-写并成一次
    str     r3, [r0]
    bx      lr
```

字段带 `volatile`（CMSIS `__IO` 的等价写法）后变成三组 `ldr/orr/str`。对普通内存两者等价；对外设不等价：有的寄存器每写一次就触发一次动作（压 FIFO、启动一次转换、打一个脉冲），折叠写入等于少发了两个动作。优化器没有重排，它直接并了。

#### 现场 4：volatile 保证访存，不保证原子

```c
volatile unsigned int shared_flag;
void isr_toggle(void) { shared_flag ^= 1u; }
```

`-O2` 下 M4 摊成三条：

```asm
isr_toggle:
    ldr     r3, [r2, #8]       ; 读
    eor     r3, r3, #1         ; 改
    str     r3, [r2, #8]       ; 写
    bx      lr
```

三条指令之间有两个可被打断的间隙：主循环读到旧值后被中断抢占，中断改了值，主循环回来把基于旧值算出的结果写回，中断的更新就地蒸发。x86 那份是一条 `xorl $1, shared_flag(%rip)`，看起来是一步，实际仍是读-改-写三步，没有锁前缀就不原子。volatile 一个字都没帮上。

### volatile 管什么、不管什么

| 需求 | volatile 够不够 | 该用什么 |
| --- | --- | --- |
| 轮询硬件标志位直到置位 | 够 | `volatile` 对象 + 循环 |
| 读一个寄存器全部位再决定 | 够 | `volatile` 结构体字段 |
| 中断置标志、主循环读快照（32 位对齐单次访问） | 够 | `volatile` + 单个标志位 |
| 主循环与中断都对同一变量读-改-写 | 不够 | 临界区（关中断/挂起调度）、外设侧原子入口（如 BSRR）、位原子操作 |
| 先配 A 再配 B，顺序不能乱 | 不够 | 内存屏障 `DMB/DSB/ISB`，CMSIS-Core 封成 `__DMB()/__DSB()/__ISB()` |
| DMA 写的缓冲区 CPU 随后读 | 不够 | 屏障 + cache 清理/无效化（带数据 cache 的核，如 ESP32-S3） |

这五道题对着上面的合同出，做完再往下走。

<QuizBank chapter="c03-volatile" />

### const 与 volatile：两个限定词各管一件事

`const` 锁的是写权限，`volatile` 锁的是访存方式，两者正交，可以同时出现。读声明仍是从变量名出发向右再向左，看限定词贴在 `*` 的哪一侧：

| 写法 | 锁住的 | 典型用途 |
| --- | --- | --- |
| `const uint32_t *p` | `*p = x` | 只读查表、输入参数 |
| `uint32_t * const p` | `p = &b` | 固定指向的句柄 |
| `const volatile uint32_t *p` | 程序不许写，且每次读都真访存 | 只读状态寄存器（如 `IDR`、`SR`） |
| `volatile uint32_t * const p` | 指针锁死、目标每次真访存 | 外设寄存器块句柄 |

`const volatile` 不是自相矛盾：`volatile` 说的是硬件可能绕过编译器改它，`const` 说的是本程序不该写它。CMSIS 的 `GPIO_TypeDef` 用 `__IO`（即 `volatile` 的封装）声明整组寄存器；读 `IDR` 这类只读寄存器时，`const volatile` 才是完整语义。

两个常见误会。其一，`const` 不等于编译期常量：`const int n = 5;` 仍是对象，只是不可写，地址与段归属照旧，`const` 大数组还会被放进 Flash（[第 1 章](./01-c-memory-model.md)算过这笔 RAM 账）。其二，`volatile` 不改变变量的段归属和地址，只改每一次访问的方式。用强制转换去掉真 `const` 对象的限定再写，是未定义行为，编译器可以按“你不会这么干”继续优化。

### UB：编译器拿“你不会越界”当燃料

C 标准把程序行为分成定义良好的、实现定义的、未指定的，第四类是未定义行为：标准直接撒手，行为可以是任何东西，包括“看起来正常工作”。这不是疏忽，是刻意的交易：把某些情形划成不许发生，编译器才能拿这条禁令当优化燃料。

教科书案例：

```c
int is_bigger_after_inc(int x) { return x + 1 > x; }   /* x = INT_MAX 时溢出，UB */
```

数学上这个比较只在 `x = INT_MAX` 时为假，而那一刻 `x + 1` 已经溢出。编译器的推理链很短：你保证不喂我 INT_MAX，那这个比较永远为真，函数可以整段折成 `return 1`。ARM 交叉汇编（arm-none-eabi-gcc 15.2.1，`-mcpu=cortex-m4 -O2`）：

```asm
is_bigger_after_inc:
    movs    r0, #1             ; 整个函数只剩装载常量
    bx      lr
```

加法、比较都被“你不会溢出”这条假设吃掉了。`-fwrapv` 把有符号溢出重新定义为按补码回绕，编译器失去假设权，只能真算：

```asm
is_bigger_after_inc:
    mvn     r3, #-2147483648   ; r3 = INT_MAX
    subs    r0, r0, r3
    it      ne
    movne   r0, #1
    bx      lr
```

宿主实测三档（gcc 16.1.0）：

| 编译档 | `is_bigger_after_inc(INT_MAX)` | 解释 |
| --- | --- | --- |
| `-O0` | 1 | gcc 16 在 `-O0` 也做函数体内折叠 |
| `-O2` | 1 | 恒真折叠 |
| `-O2 -fwrapv` | 0 | 溢出按回绕，INT_MAX+1 = INT_MIN，比较为假 |

`-O0` 那一行是本章最该记住的反例。把宿主 `-O0` 汇编拉出来，函数体是 `pushq %rbp; movq %rsp, %rbp; movl %ecx, 16(%rbp); movl $1, %eax; popq %rbp; ret`，加法与比较都不在，只剩装载常量；`main` 里仍规规矩矩 `call`，可被调用的函数已经不算账了。`-O0` 不等于逐行照实执行，它只是不在调用点做折叠、不在函数间传播。

![UB 编译器优化陷阱：源代码 → 编译器假设无 UB → 折叠为常量 → 运行时与数学期望偏离](/anim/ub-compiler-trap.svg)

另一个方向是崩溃。数组越界、空指针解引用、未对齐访问，这些 UB 在 ARM 上会直接触发 HardFault；用宿主侧 `-fsanitize=undefined` 或嵌入式侧 `-fstack-protector` 提前抓人，比等 HardFault 再查省力。

### 移位雷区：最便宜也最频繁的一刀

移位是嵌入式使用频率最高的运算，每个寄存器掩码都是它，也是 UB 密度最高的运算。标准划了三条红线：

1. 移位计数 ≥ 操作数位宽：UB，与操作数有无符号无关，`1u << 33` 同样踩线；
2. 移位计数为负：UB；
3. 左移把 1 移进或移出有符号数的符号位：UB，如 `(int)1 << 31`。

`shift_oob(1u, 33u)` 的实测读数：`-O0` 是 2，`-O2` 是 0。`-O0` 为什么是 2？真机指令就在那儿跑：x86 的 `shl` 与 Cortex-M 的 `lsl` 都把计数截到操作数位宽的低 5 位，`33 & 31 = 1`，`1u << 1 = 2`。`-O2` 为什么是 0？编译器认出 UB，结果可以任意，它选了最省指令的那个。两个答案都不算错，UB 题目本身没有标准答案。

掩码的安全写法是三层设防：

- 字面量类型先行：`1` 是 int，`1 << 31` 踩红线 3；写 `1UL` 只防住符号位问题，防不住计数越界；
- 计数必须可证小于位宽：`1UL << (LED_R_PIN + 16)` 里 `LED_R_PIN` 是枚举常量，加 16 后是 22/23/24，编译期可见；
- 运行期计数先检查再移位：

```c
if (n < 32u) {
    mask = 1u << n;        /* 计数已证 < 位宽 */
} else {
    return false;
}
```

计数类型也要管：有符号负数在“检查前”就已经踩了红线 2，`int8_t` 的计数先转 `unsigned` 再查范围。`-fwrapv` 只救有符号加/减/乘的溢出，移位三条红线一条都不救：`-fwrapv -O2` 下 `1u << 33` 依旧是 0。

### 严格别名：float 与 uint32 互看

C 规定访问对象必须用兼容类型的左值表达式，少数例外：`char *` 谁都能指、加过限定符的同类型、union 自己的成员。拿 `uint32_t *` 去解引用一个 `float` 对象，就是严格别名违规。它十年都不一定发作，因为编译器只是基于“这两个指针不重叠”的假设做优化：把两次 float 读合并成一次，或把 store 重排到 load 前面；你的代码在这条假设上打洞。

违规现场会被警告抓住（alias-violate.c 第 13 行）：

```text
warning: dereferencing type-punned pointer will break strict-aliasing rules [-Wstrict-aliasing]
```

两种合法写法：

```c
/* 读法一：union 双关，C11 起脚注给出位模式重解释的正式说法 */
static uint32_t bits_union(float f)
{
    union { float f; uint32_t u; } pun;
    pun.u = 0u;
    pun.f = f;
    return pun.u;
}

/* 读法二：memcpy，标准层面永远合法，优化后就是一条 load */
static uint32_t bits_memcpy(float f)
{
    uint32_t u;
    memcpy(&u, &f, sizeof u);
    return u;
}
```

两者位级一致：`bits_union(1.0f) = 0x3F800000`，`bits_memcpy(1.0f) = 0x3F800000`。选型很朴素：跨类型取位优先 `memcpy`，零心智负担；既取位又想省一次拷贝用 union，但要记住它依赖“同存储、同对齐”的实现约定；字节序敏感（网络协议、EEPROM 布局）走 `unsigned char *` 逐字节拼，char 是别名规则的天生例外。

![严格别名：指针强转是 UB，union/memcpy 才是合法写法](/figures/c-07-strict-alias.svg)

外设寄存器不属于这个学科：`*(volatile uint32_t *)0x40021418` 是“本来就该用正确的类型读正确的地址”。别名规则管的是同一块存储的两种身份，不是“我 cast 了一个外设指针”。

### MISRA 边界：把可任意解释的地带收窄

MISRA-C:2012 全本 300 多条，汽车与医疗行业做全量合规。嵌入式自用的取法是：把历史上真实炸过的 UB 高发区画成红线，剩下的按团队成本自选。来源 C7 选了十条，共同句式是：把编译器可以任意解释的地带，用写法约束收窄成只有一种读法。

| # | 约束 | 对应的雷 |
| --- | --- | --- |
| 1 | 声明即初始化 | 读未初始化变量是 UB |
| 2 | 隐式转换显式化 | 有符号/无符号混算与整型提升 |
| 3 | 移位计数先验证 | 上节三条红线 |
| 4 | 位运算与比较不裸混 | `flags & MASK == MASK` 解析成 `flags & (MASK == MASK)` |
| 5 | 禁递归 | 裸机栈一帧一帧，没有哨兵 |
| 6 | 指针运算只在数组圈内 | 解引用尾后一位、跨对象指针差都是 UB |
| 7 | 禁 goto 直穿初始化 | 跳过初始化等于读未初始化 |
| 8 | switch 必有 default | 新增枚举值不许悄悄漏 |
| 9 | volatile 纪律 | 外设寄存器与 ISR 共享变量必须 volatile；但它不解决原子性 |
| 10 | 无副作用依赖 | `&&` 与逻辑或的右侧、`if` 条件里的副作用不许是程序依赖的一部分 |

边界要说清：这十条是自选清单，不是 MISRA 合规证书；MISRA 也不能替代编译器，它约束写法，抓现行仍靠警告与静态分析。三道防线按成本排：`-Wall -Wextra`（配 `-Werror` 进 CI）零成本；`-Wconversion -Wsign-conversion`、`-Wstrict-aliasing`、`-Warray-bounds`、`-Wuninitialized`、`-fstack-usage` 是专项；cppcheck、clang-tidy、gcc `-fanalyzer` 看数据流。UBSan 在宿主上最有效，来源记录的 MinGW gcc 16.1.0 没带运行库，交叉链支持也有限，所以嵌入式的主战场是第一、三道防线。

## 测量与证据

本章所有数字来自来源 C3、C7 的实测记录，两套工具链同日取证：宿主 MinGW-Builds gcc 16.1.0（x86_64-posix-seh），交叉 xPack arm-none-eabi-gcc 15.2.1（`-mcpu=cortex-m4 -mthumb`），编译旗 `-std=c11 -Wall -Wextra`，零告警。换编译器、换版本、换优化档，指令形状会变，判读方法不变。

| 取证项 | 命令 | 来源记录里的结果 |
| --- | --- | --- |
| 轮询被缓存 | `arm-none-eabi-gcc ... -O2 -S`，搜 `poll_plain` | 整函数只读一次，`.L3: b .L3` |
| 轮询保命 | 同上，搜 `poll_volatile` | 每圈一次 `ldr` |
| 延时被删 | 同上，搜 `delay_plain` | `ret` / `bx lr` |
| 延时保命 | 同上，搜 `delay_volatile` | 计数落栈槽，每圈 `ldr/subs/str` |
| 写被合并 | 同上，搜 `cfg_plain` / `cfg_volatile` | 一次 `orr #7` vs 三组 `ldr/orr/str` |
| 非原子读-改-写 | 同上，搜 `isr_toggle` | M4 三条指令、两个间隙 |
| 溢出折叠 | `sh probe.sh` 第 5 步 | `movs r0, #1` |
| 三档读数 | `sh probe.sh` 第 1、2 步 | 1 / 1 / 0 |
| 移位两档变脸 | 同上 | 2 / 0 |
| 合法位读法 | `probe.c` 的 `bits_union` / `bits_memcpy` | 均 `0x3F800000` |
| 别名违规警告 | `probe.sh` 第 3 步 | `-Wstrict-aliasing` |
| 越界与未初始化警告 | 同上 | `-Warray-bounds=`、`-Wuninitialized` |

`00-blink` 的六个变体是另一组证据。同一份 `main.c`，只动三处 volatile（寄存器宏、`delay` 参数、`__asm__ volatile ("nop")`），`-O2` 下的编译期结果：

| 变体 | 宏 | 参数 | nop | `-O2` 下 `main` 的长相 | 灯 |
| --- | --- | --- | --- | --- | --- |
| A（现状） | 有 | 有 | 有 | 先写 `RCC_AHB1ENR` 开时钟，再配 MODER | 闪 |
| B | 有 | 无 | 有 | 循环仍在（`nop / subs / bne`） | 闪 |
| C | 有 | 无 | 无 | 延时消失，两条 `BSRR` 写紧挨着 | 不闪 |
| D | 有 | 有 | 无 | 循环保留，计数在寄存器 r3 | 闪 |
| F | 无 | 有 | 有 | 顺序倒了：先读 `GPIOF_MODER`，后开时钟 | 未知 |
| E | 无 | 无 | 无 | `main:` 只剩一条 `b.n 0` | 全黑 |

三点读法：

1. B 行纠正一个流行说法：去掉 `delay` 参数的 volatile，灯照闪，因为 `__asm__ volatile ("nop")` 独立挡住了删除。要复现翻车，得连 `nop` 一起删（C 行）。
2. F 行比 C 行更常见也更阴：漏的是寄存器宏里一个词，现象不是不闪，而是偶尔配不上、换颗芯片就不好使。
3. D 行说明 volatile 保的是“每次使用都可见”，不是“必须占一块内存”：`delay` 是 static 且被内联，计数留在寄存器；MMIO 不受影响，地址硬编码，编译器无处可藏。

自查漏没漏 volatile，一条命令数宏展开后的结果：

```bash
arm-none-eabi-gcc -mcpu=cortex-m4 -E main.c | grep -c 'volatile uint32_t'
```

`00-blink` 现状是 9；只漏寄存器宏是 1；三处全漏是 0。数的是展开结果，不是源文件行数，宏里的 volatile 写在头文件里，源码 grep 看不全。

板上那一步要标注清楚：来源记录写明六个变体的编译期结果已全部实测，板上肉眼现象本轮未跑（写那一版时手边没有接上 F407 与 ST-Link）。有板的人可以按变体表复跑：`-O0` 改 `-O2` 先烧 A 行，灯应照闪；再去掉参数 volatile 与 nop（C 行），PF6 应恒定或只剩极窄脉冲，而不是 1 Hz 方波。

判断“真的会了”：给你一段驱动代码，能在 30 秒内生成 `-O0/-O2` 两份汇编，指出哪一次读被缓存、哪一次写被删、哪一组读-改-写被合并；再给你一个 volatile 变量，能说清它防的是哪类风险，答不出来源就知道是性能税。

## 失败分支

| 现象 | 原因 | 区分证据 | 下一动作 |
| --- | --- | --- | --- |
| `-O0` 一切正常，发布档翻车 | 优化器按 as-if 删改访存 | 同档复现，查 `-O2` 汇编 | 功能验证至少跑一遍与发布一致的 `-O` 档 |
| 轮询循环原地死转 | 标志没加 volatile，只读一次 | 汇编里 `.L3: b .L3`，循环内无访存 | 标志对象加 volatile |
| 延时变 0 | 空循环无副作用，计数非 volatile | `delay_plain` 只剩 `ret`/`bx lr` | 计数 volatile，或循环体放 `__asm__ volatile` |
| 照抄“去掉 delay 的 volatile 灯就不闪” | 循环体里的 `asm volatile` 独立兜底 | B 行：灯照闪 | 连 nop 一起去掉才复现（C 行），结论自己跑一遍 |
| 配置顺序反了、换芯片才复发 | 寄存器宏漏 volatile | F 行：先读 MODER 后开时钟 | 用 CMSIS `__IO` 结构体，或给宏补 volatile |
| 所有外设写被删光 | 宏、参数、nop 三处全漏 | E 行：`main` 只剩 `b.n 0` | 同上，并跑展开计数 |
| 拿 volatile 当锁 | 它不保证原子与顺序 | M4 `isr_toggle` 三条指令两个间隙 | 临界区、只置位/只清位协议、BSRR |
| 给大缓冲全标 volatile | 每次访问都真访存，块搬运被拆碎 | 反汇编里 `memcpy` 变成逐字节 | 回到“谁会绕过编译器改这块内存” |
| 以为 volatile 能管 cache | 数据 cache 与 DMA 的一致性另有机制 | ESP32-S3 上 DMA 缓冲读到旧数据 | 屏障 + cache 清理/无效化 |
| `x + 1 > x` 对 INT_MAX 返回 1 | 有符号溢出是 UB，编译器折叠 | `movs r0, #1`；`-fwrapv` 下变 0 | 做边界检查，或改用无符号/更宽类型 |
| `1u << 33` 两档两个答案 | 计数 ≥ 位宽是 UB | `-O0` 是 2，`-O2` 是 0 | 计数先证明小于位宽 |
| float 位模式读出乱值 | 指针强转违反严格别名 | `-Wstrict-aliasing` 警告 | 改用 union 或 memcpy |
| 以为 `-fwrapv` 能包打天下 | 它只管有符号加/减/乘 | `-fwrapv -O2` 下 `1u<<33` 仍是 0 | 移位单独做计数检查 |

## 离开检查

1. `-O2` 把轮询循环变成 `b .L3`，编译器依据的是哪条规则？volatile 收回了哪三项授权？
2. `delay_plain` 为什么会被删成一条 `ret`？`-O0` 下它为什么“看起来正常”？
3. 主循环 `flag ^= 1`、中断 `flag = 0`，`flag` 已是 volatile，为什么仍会丢更新？给出两种修法。
4. `const volatile uint32_t *p` 与 `volatile uint32_t * const p` 各锁住什么？各举一个寄存器场景。
5. `is_bigger_after_inc(INT_MAX)` 在 `-O0`、`-O2`、`-O2 -fwrapv` 下各返回什么？`-O0` 的读数说明了什么？
6. `1u << 33` 在 `-O0` 与 `-O2` 下各是多少？为什么 `-fwrapv` 救不了它？写出安全的掩码写法。
7. 用 `*(uint32_t *)&f` 读 float 的位模式错在哪？两种合法写法各依据什么？

<details>
<summary>对照答案</summary>

1. as-if 规则（N1570 §5.1.2.3）：可观察行为不变，指令随便排。volatile 收回缓存、删除、合并三项授权。
2. 空循环无副作用，C11 起编译器可假定其终止；计数非 volatile，比较结果可缓存折叠。两层权利叠加，整个循环消失。`-O0` 不在调用点折叠、不做函数间传播，所以每圈真读，看起来正常。
3. volatile 只保证读-改-写三步真访存，不保证三步之间不被抢占。修法：临界区包住读-改-写；改成只置位/只清位协议；或用外设侧原子入口（BSRR）。
4. 前者锁写权限（程序不许写）且每次读真访存，用于只读状态寄存器；后者锁指针本身，目标保持 volatile，用于固定外设基址句柄。
5. 1、1、0。`-O0` 也折叠，说明“`-O0` 能跑”不是正确性证据；`-fwrapv` 把溢出定义为回绕，比较为假。
6. `-O0` 是 2（计数被截到低 5 位，`33 & 31 = 1`），`-O2` 是 0（UB 之后编译器任选）。`-fwrapv` 只管有符号加/减/乘。安全写法：`1UL << (LED_R_PIN + 16)` 且计数编译期可证小于 32；运行期计数先 `if (n < 32u)` 再移。
7. 用不兼容类型的左值访问 float 对象，违反严格别名规则，编译器可基于“这类访问不存在”做合并与重排。合法写法：union 双关（C11 脚注的位模式重解释）与 memcpy（对象表示复制，优化后是一条 load）。

</details>

动作验收：在自己的工程上把 `-O0` 与发布档各编一次，对同一段外设访问生成两份汇编，指出被缓存、被删、被合并的访存；再写一个掩码函数，让计数在编译期是枚举常量、运行期走范围检查，两版都过 `-Wall -Wextra -Werror`。


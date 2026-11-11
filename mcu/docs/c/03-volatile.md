---
title: C3 volatile：跟编译器约法三章
status: done
difficulty: 3
minutes: 70
---

# C3 volatile：跟编译器约法三章

> 🎯 同一段轮询，`-O0` 跑得好好的，`-O2` 一开就死等。编译器没坏，它只是不知道那个地址后面藏着一台会自己变状态的机器。

## 本章精髓

1. **为什么优化会"吃掉"访存**：编译器按 as-if 规则工作，只要可观察行为不变，缓存、删除、合并你的读写都合法。它眼里的 `status` 是一块内存；而 `USART1->SR` 后面是硬件，你不读它也在变。`volatile` 就是收回这项授权的合同条款。
2. **为什么 volatile 只解决一半问题**：它保证"每次使用都真实访存"，不保证"这一串访存之间没人插队"。把 `volatile int flag` 当锁用，是把类型限定符当成了同步原语。
3. **为什么值得单独一章**：本站所有"库源码逐行解析"读的都是带 volatile 的封装（CMSIS 的 `__IO`、SPL 的 `__IO` 局部变量、IDF 的寄存器访问）。懂它的合同与边界，才知道那些封装在替谁兜底。

<details>
<summary>🌐 English Abstract</summary>

**Why volatile matters**: The compiler's as-if rule allows it to cache, delete, or merge memory accesses as long as observable behavior stays the same. But hardware registers change state independently—`volatile` revokes the compiler's authorization to optimize those accesses. **What volatile guarantees**: Every use triggers an actual memory access. **What it doesn't guarantee**: Atomicity or ordering—`volatile int flag` is not a synchronization primitive. **Three must-have scenarios**: (1) Hardware registers (MMIO), (2) Interrupt-shared variables, (3) Signal handlers. **Two anti-patterns**: (1) Using volatile as a lock, (2) Adding volatile to "fix" race conditions (use atomics/critical sections instead).

</details>

- **能记住**：volatile 的"管三件事 / 不管两件事"清单（本章记忆锚点）
- **能理解**：为什么 `-O2` 把轮询变成原地空转、把延时循环删成一条返回——四段本机取证汇编，x86-64 与 Cortex-M4 各一份
- **能用**：拿到驱动代码能判断哪里的 volatile 必需、哪里的是性能税；知道中断共享变量该换什么机制

## 先修

- [C2 指针](02-pointer.md)：`(volatile uint32_t *)0x40021418` 里限定符该贴谁；
- [B1 四步构建](../build/01-four-steps.md)：`-O` 在编译层起作用，本章的翻车全发生在编译这一步；
- [S3 GPIO](../stm32/03-gpio.md) 的 ODR 读-改-写隐患：同一个问题在外设侧的另一种表现。

## 先跑起来（10 分钟 quick win，**不用开发板**）

```bash
cd code/c/03-volatile
gcc -std=c11 -Wall -Wextra -O2 -S -o opt_probe.O2.s opt_probe.c
arm-none-eabi-gcc -std=c11 -Wall -Wextra -mcpu=cortex-m4 -mthumb -O2 -S -o opt_probe.m4.O2.s opt_probe.c
```

跑之前先押：那个空转一千圈的延时函数，在优化后的产物里会剩几条指令？总该留下点什么吧。押个数字再搜，命中率通常低得让人印象深刻。

没有 ARM 工具链只跑第一条也够。两条命令产物里搜 `delay_plain`：x86 那份整个函数只剩一条 `ret`，Cortex-M4 那份只剩一条 `bx lr`。你写的 `while (n--) {}` 一千圈延时，在优化器眼里根本没存在过。这就是本章的全部主题，后面四十分钟是解释它为什么合法、以及怎么避免。

## 动画：同一段轮询的两条命运

![volatile 的访存合同：读一次 vs 每次读](/anim/volatile-as-if.svg)

## 视频讲解

本章有配套视频（约 12 分钟），用 4 个犯罪现场、6 个变体实验把 volatile 讲透。视频将在 B 站发布后在此更新链接。

视频的分幕、旁白与动画绑定见 [`video/episodes/c3-volatile/episode.json`](https://github.com/zhuguang-ZFG/STM32/blob/main/mcu/video/episodes/c3-volatile/episode.json)（成片的唯一事实源，渲染脚本只吃这一个文件），写作阶段的分镜见 [`storyboard.md`](https://github.com/zhuguang-ZFG/STM32/blob/main/mcu/video/episodes/c3-volatile/storyboard.md)。两个都在仓库里，未发布到站点。

四阶段：优化器的世界观 → 不加 volatile 的下场 → 加 volatile 的下场 → 边界在哪里。

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 一、as-if：优化器的世界观 | C 标准给编译器的授权书；volatile 收回哪三项授权 | 配置（语义规则） |
| 二、四个现场取证 | 轮询 / 延时 / 写合并 / 共享标志，`-O0` 与 `-O2` 汇编逐条对账（x86-64 与 Cortex-M4 各一份） | 代码分析 |
| 三、管什么与不管什么 | "每次必登门"三条保证 vs 原子性与顺序性两个空白 | 配置 + 代码分析 |
| 四、库源码解析 | CMSIS `GPIO_TypeDef` 的 `__IO`、SPL 的 `__IO` 局部变量、IDF 的对应做法 | 库解析 |
| 五、代码分析：`00-blink` | 逐行看三处 volatile：寄存器宏、`delay` 参数、`__asm__ volatile ("nop")` | 代码分析 |
| 六、补齐边界 | 临界区、外设侧原子寄存器、屏障与 cache 各自站哪个岗 | 库解析 |

> 本章不涉及引脚设置：`volatile` 是语言层的合同，作用域覆盖**所有** MMIO 访问，与具体引脚无关。

## 一、as-if：优化器的世界观

C 标准（ISO/IEC 9899:2018，类型限定符在 §6.7.3、程序执行语义在 §5.1.2.3，具体措辞以你手上的标准版本为准）给编译器的授权是：**只要可观察行为不变，中间的机器指令随你怎么排**。

于是优化器做三件天经地义的事：

| 优化动作 | 对普通内存 | 对硬件寄存器 |
|---|---|---|
| 缓存：多次读合成一次，值留在寄存器 | 完全正确 | **错**——这几次读之间硬件自己变了 |
| 删除：写了没人再读的赋值（死 store） | 可以删 | **错**——那次写本身就是目的 |
| 合并：连续两次 `|=` 合成一次 | 等价 | **错**——硬件要两个动作，你只发了一个 |

`volatile` 的语义就是把这三项授权收回：**每次使用都必须真实访存，不许缓存、不许删、不许凭空造**。注意它只管"访存"这一件事，不改值的含义，它不是 `atomic`，也不是锁。

另有一条常被忽略：**没有副作用的空循环，编译器可以假定它不会无限跑**（C11 起此类循环按未定义处理）。这解释了下一节的 `delay_plain`，它连"缓存"都没用上，直接整个消失。

![编译器把 flag 缓存进寄存器，ISR 在内存里写 1；轮询循环因此看不到更新](/figures/c-03-volatile.svg)

## 二、四个现场取证

取证环境（两套工具链，同日实测，均 `-std=c11 -Wall -Wextra` 零告警）：宿主 MinGW-Builds **gcc 16.1.0**（x86_64-posix-seh）与 **xPack arm-none-eabi-gcc 15.2.1**（`-mcpu=cortex-m4 -mthumb`，就是你板子上那颗 M4 的目标后端）。下面每个现场都摆两份：**x86 那份方便你本机 30 秒复现，Cortex-M4 那份才是你板子上真正会跑出来的东西**。两边的优化决策一模一样：同一个优化器、同一条 as-if 规则，只是指令形式不同。

### 现场 1：轮询状态位——读一次 vs 每次读

源码只有一处差别：`unsigned int` 与 `volatile unsigned int`。

`-O0` 下的 `poll_plain`，每圈都真访存（这才是"-O0 能跑"的真相）：

```asm
poll_plain:
.L2:
    movl    g_status(%rip), %eax     ; 每圈真的去内存读
    andl    $1, %eax
    testl   %eax, %eax
    je      .L2                      ; 没置位就再来一圈
    movl    $42, %eax
```

同一函数在 `-O2` 下（x86-64）：

```asm
poll_plain:
    testb   $1, g_status(%rip)       ; 整段代码只读这一次
    je      .L3
    movl    $42, %eax
    ret
.L3:
    jmp     .L3                      ; 原地死转，再也不看那块内存
```

判断依据被缓存了：bit0 后来被硬件置成 1，代码不会知道。

换到 Cortex-M4（`-O2`），同一件事，指令形式不同：

```asm
poll_plain:
    ldr     r3, .L5
    ldr     r3, [r3]                 ; 整个函数只读这一次
    lsls    r3, r3, #31              ; 把 bit0 顶到符号位
    bpl     .L3                      ; 没置位 → 跳 .L3
    movs    r0, #42
    bx      lr
.L3:
    b       .L3                      ; 死转：连那块内存都不再碰
```

注意 M4 这份的残酷之处：`.L3: b .L3` 是**一条指令的紧死循环**，没有访存、没有中断以外的出口。板子看起来"活着"（SWD 还能连），但这段代码永远不会往下走。这就是"轮询少了 volatile"在真实芯片上的长相。

换成 `poll_volatile`，`-O2` 下循环回到每圈访存：

```asm
poll_volatile:                       ; x86-64
.L6:
    testb   $1, v_status(%rip)       ; 每圈一次真实读
    je      .L6
    movl    $42, %eax
    ret
```

```asm
poll_volatile:                       ; Cortex-M4
.L8:
    ldr     r3, [r2, #4]             ; 每圈一次真实 ldr
    lsls    r3, r3, #31
    bpl     .L8
    movs    r0, #42
    bx      lr
```

### 现场 2：软件延时——整个循环被删

`delay_plain(unsigned n){ while (n--) {} }` 在 `-O2` 下的全部产物：

```asm
delay_plain:
    ret                              ; x86-64
```

```asm
delay_plain:
    bx      lr                       ; Cortex-M4：整个函数一条返回
```

一条指令，你的"500ms"变成 0ms。参数改成 volatile（`delay_volatile`）后循环保住了：

```asm
delay_volatile:
    movl    %ecx, 8(%rsp)            ; x86-64：计数落在内存（栈槽），不放寄存器
.L11:
    movl    8(%rsp), %eax
    leal    -1(%rax), %edx
    testl   %eax, %eax
    movl    %edx, 8(%rsp)            ; 每圈写回
    jne     .L11
    ret
```

```asm
delay_volatile:
    sub     sp, sp, #8
    str     r0, [sp, #4]             ; Cortex-M4：计数落栈槽
.L15:
    ldr     r3, [sp, #4]
    subs    r2, r3, #1
    str     r2, [sp, #4]             ; 每圈写回
    cmp     r3, #0
    bne     .L15
    add     sp, sp, #8
    bx      lr
```

延时的另一条出路是**给它真实副作用**：`00-blink` 用的是 `__asm__ volatile ("nop")`，见第五节。

### 现场 3：配置序列被合并成一次写

三个连续 `|=` 想表达"依次置位三个使能位"。普通结构体（等于寄存器访问漏了 volatile）：

```asm
cfg_plain:
    orl     $7, (%rcx)               ; x86-64：三次读-改-写 → 一次，写进去 7
    ret
```

```asm
cfg_plain:
    ldr     r3, [r0]                 ; Cortex-M4：三次并成一次
    orr     r3, r3, #7               ;   M4 没有"内存读-改-写"单指令，
    str     r3, [r0]                 ;   所以整段只访存两次
    bx      lr
```

字段带 `volatile`（CMSIS `__IO` 的等价写法）：

```asm
cfg_volatile:
    orl     $1, (%rcx)               ; x86-64：三条独立读-改-写
    orl     $2, (%rcx)
    orl     $4, (%rcx)
    ret
```

```asm
cfg_volatile:
    ldr     r3, [r0]                 ; Cortex-M4：三组 ldr/orr/str
    orr     r3, r3, #1
    str     r3, [r0]
    ldr     r3, [r0]
    orr     r3, r3, #2
    str     r3, [r0]
    ldr     r3, [r0]
    orr     r3, r3, #4
    str     r3, [r0]
    bx      lr
```

对普通内存两者等价；对外设**不等价**：有的寄存器每写一次就触发一次动作（压 FIFO、启动一次转换、打一个脉冲）。折叠写入 = 少发了两个动作。这也是"顺序"问题的另一种形态：优化器没重排，它直接**并了**。

### 现场 4：volatile 保证访存，不保证原子

```c
volatile unsigned int shared_flag;
void isr_toggle(void) { shared_flag ^= 1u; }
```

`-O2` 下：

```asm
isr_toggle:
    xorl    $1, shared_flag(%rip)    ; x86-64：一条指令，仍是"读-改-写"三步
    ret
```

```asm
isr_toggle:
    ldr     r3, [r2, #8]             ; Cortex-M4：连"一条指令"的假象都没有
    eor     r3, r3, #1               ;   读、改、写摊成三条
    str     r3, [r2, #8]
    bx      lr
```

`volatile` 让这次访问真的发生了，**但不阻止中断在这三步中间插进来**：主循环读到旧值后被抢占、中断改了值、主循环回到"写"这步把带旧值的成果写回去。中断的动作就地蒸发。`volatile` 一个字都没帮你。M4 这份反汇编值得多看一眼：三条指令之间有两个可被打断的间隙，而 x86 那份"看起来一条指令"也绝不原子（x86 的内存读-改-写只在锁前缀下才保证原子）。这是本章最容易出事故的一点，第六节给替代方案。

## 三、管什么与不管什么

| 需求 | volatile 够不够 | 该用什么 |
|---|---|---|
| 轮询硬件标志位直到置位 | **够** | `volatile` 对象 + 循环 |
| 读一个寄存器全部位再决定 | 够 | `volatile` 结构体字段 |
| 中断置标志、主循环读快照（32 位对齐单次访问） | 够 | `volatile` + 单个标志位 |
| 主循环与中断都对同一变量做读-改-写 | **不够** | 临界区（关中断/挂起调度），或外设侧原子入口（GPIO 的 BSRR），或位原子操作 |
| 先配 A 再配 B，顺序不能乱 | 不够（访存都保，但相对顺序与预取仍可能不如你预期） | 内存屏障：Cortex-M 的 `DMB/DSB`，CMSIS-Core 的 `__DMB()/__DSB()/__ISB()` 封装 |
| DMA 写的缓冲区 CPU 随后读 | 不够 | 屏障 + cache 清理/无效化（带数据 cache 的核，如 ESP32-S3；API 以 ESP-IDF 文档为准） |

## 四、库源码解析：volatile 藏在哪一层

**CMSIS 设备头**把 volatile 写进结构体字段。`stm32f407xx.h:526-537`（本项目引证副本原文）：

```c
typedef struct
{
  __IO uint32_t MODER;    /*!< GPIO port mode register,               Address offset: 0x00      */
  __IO uint32_t OTYPER;   /*!< GPIO port output type register,        Address offset: 0x04      */
  __IO uint32_t OSPEEDR;  /*!< GPIO port output speed register,       Address offset: 0x08      */
  __IO uint32_t PUPDR;    /*!< GPIO port pull-up/pull-down register,  Address offset: 0x0C      */
  __IO uint32_t IDR;      /*!< GPIO port input data register,         Address offset: 0x10      */
  __IO uint32_t ODR;      /*!< GPIO port output data register,        Address offset: 0x14      */
  __IO uint32_t BSRR;     /*!< GPIO port bit set/reset register,      Address offset: 0x18      */
  __IO uint32_t LCKR;     /*!< GPIO port configuration lock register, Address offset: 0x1C      */
  __IO uint32_t AFR[2];   /*!< GPIO alternate function registers,     Address offset: 0x20-0x24 */
} GPIO_TypeDef;
```

`__IO` 是 CMSIS-Core 的宏，本质是 `volatile` 的封装（同族还有只读/只写的变体；定义在 `cmsis_compiler.h`/`cmsis_gcc.h`，本项目 ref 只入了设备头，核心头以你手上的 CMSIS 版本为准）。这个设计的价值在于：**声明一次，管住整组寄存器**。应用写 `GPIOF->BSRR = ...`（`GPIOF` 即 `((GPIO_TypeDef *) GPIOF_BASE)`，同文件 :1107）根本不需要操心限定符。

**SPL（StdPeriph）** 则在函数内部手动加。`stm32f4xx_i2c.c:1261-1264`（引证副本原文）：

```c
FlagStatus I2C_GetFlagStatus(I2C_TypeDef* I2Cx, uint32_t I2C_FLAG)
{
  FlagStatus bitstatus = RESET;
  __IO uint32_t i2creg = 0, i2cxbase = 0;
```

停下来想一层：**两个局部变量为什么要写 `__IO`？** 它们的值由本函数算出，硬件改不到；真正的保底来自 `I2C_TypeDef` 字段自带的 volatile。所以这两处是"作者求稳"的防御写法，代价是变量被钉在内存里（每次读写都访存），功能收益接近零。

这不是挑 SPL 的毛病，而是本章最该学走的读码动作：**看到一个 volatile，先问"谁会绕过编译器改这块内存"。答得出来是必需，答不出来是性能税。** 对照 [S11 I2C](../stm32/11-i2c.md) 里 SPL 的轮询实现，你能同时看到"必需的"和"可加可不加的"两种写法。

**ESP-IDF** 同一路线：寄存器访问由带 volatile 的字段/宏完成，驱动层再向上封装。[P6 SPI/I2C 驱动框架](../esp32/06-spi-i2c-driver.md) 里应用侧碰不到裸地址；一旦你下探到 LL 层或自己写外设访问，volatile 立刻回来。

## 五、代码分析：`00-blink` 里的三处 volatile

本节不重复贴板级工程，逐行看现有的 `code/stm32/00-blink/main.c`。它的 `Makefile:20` 是 `CFLAGS := $(MCU) -O0 -g3 ...`，"让第一次上板不被优化器打扰"的保险设置，也正是本章要拆掉的保险。

**① 寄存器宏（`main.c:26-34`）**

```c
#define RCC_AHB1ENR         (*(volatile uint32_t *)(RCC_BASE + 0x30UL))
#define GPIOF_BSRR          (*(volatile uint32_t *)(GPIOF_BASE + 0x18UL))
```

`(*(volatile uint32_t *)(addr))` 拆开读：地址 → 转成"指向 volatile uint32_t 的指针" → 解引用。限定符作用在**被指向的对象**上，于是每次读写这个宏都是真访存。

这个 `volatile` 漏掉会怎样？把 `main.c:26-34` 六个宏里的 `volatile` 全部删掉（其余不动），`-O2` 交叉编译实测，`main` 变成这样（片段，Cortex-M4）：

```asm
main:
    ldr     r1, [pc, #104]
    ldr     r2, [pc, #108]
    ldr.w   r3, [r1, #1024]          ; 0x400 = GPIOF_MODER —— 先读了它
    ldr.w   r4, [r2, #2096]          ; 0x830 = RCC_AHB1ENR
    ldr.w   r0, [r1, #1028]          ; GPIOF_OTYPER
    orr.w   r4, r4, #32
    bic.w   r3, r3, #12288
    str.w   r4, [r2, #2096]          ; 开 GPIOF 时钟的写，排到了上面那次读之后
```

源码顺序是"先开时钟，再配引脚"，机器码顺序反过来了：**GPIOF 时钟还没使能，代码就去读 GPIOF 的寄存器**。这就是第一节表格第三行"合并/重排"的真相：优化器不是把两次写并成一次，而是把整段访问按它自己的依赖图重排（它眼里这些只是普通内存）。本工程默认 `-O0`，所以它一直是对的；这也是为什么"能跑"从来不是证据。

**② 限定符贴谁：`volatile` 在指针的哪一侧（`main.c:39`）**

```c
static void delay(volatile uint32_t count)
```

`volatile uint32_t count`：计数本身是易变对象 → 每圈 load/store（现场 2 的保命写法）。别和 `uint32_t * volatile p`（指针自身易变）混，`volatile` 在 `*` 左边和右边说的是两件事，回 [C2 指针](02-pointer.md) 对照。

**③ 语句级 volatile：`__asm__ volatile ("nop")`（`main.c:42`）**

```c
while (count--) {
    __asm__ volatile ("nop");
}
```

这里的 `volatile` 是 **asm 语句的限定符**，与对象类型限定符是两套规则：表示"这段汇编不许删、不许移动、不许合并"，同时给循环注入了副作用。所以 `00-blink` 的延时比纯 volatile 计数更稳。但周期数仍取决于主频与优化档，注释里"约 0.5s（-O0 实测校准）"就是这个意思，换时钟源要重新校准（见 [S2 RCC 时钟树](../stm32/02-rcc-clock.md)）。

**把三处 volatile 拆开逐个实测**（`arm-none-eabi-gcc 15.2.1`，`-mcpu=cortex-m4 -mthumb -O2`，`sh code/c/03-volatile/blink-variants.sh` 可全部重跑）：

| 变体 | 宏 `volatile` | 参数 `volatile` | `nop` | `-O2` 下 `main` 的长相 | 灯 |
|---|---|---|---|---|---|
| A（现状） | 有 | 有 | 有 | 先写 `RCC_AHB1ENR` 开时钟，再配 MODER | 闪 |
| B | 有 | **无** | 有 | 与 A 几乎一样，循环仍在（`nop / subs / bne`） | 闪 |
| C | 有 | **无** | **无** | 延时没了：两条 `BSRR` 写（`str [r3,#0x418]`）紧挨着 | 不闪 |
| D | 有 | 有 | **无** | 循环保留，计数却在寄存器 r3 里（无 `ldr/str`） | 闪 |
| F | **无** | 有 | 有 | 顺序倒了：读 `GPIOF_MODER` 排在开时钟那次写之前 | 未知 |
| E | **无** | **无** | **无** | `main:` 只剩一条 `b.n 0`——**所有外设写被当死 store 删光** | 全黑 |

三点读法：

1. **B 行是对流行说法的纠正**：网上讲 volatile 几乎都说"去掉 `delay` 参数的 volatile，`-O2` 灯就不闪了"。在这份代码里不成立：`__asm__ volatile ("nop")` 已经独立挡住了删除。**要复现翻车，得连 `nop` 一起删（C 行）。**
2. **F 行比 C 行更常见也更阴**：漏的是寄存器宏里一个词，现象不是"不闪"而是"偶尔配不上/换颗芯片就不好使"：顺序倒了。
3. **D 行顺带回答了"volatile 局部变量到底在不在内存"**：`delay` 是 `static` 且被内联，计数就留在寄存器；而第二节的 `delay_volatile` 是外部函数、单独编译，参数落在 `[sp,#4]` 每圈访存。**`volatile` 保的是"每次使用都可见"，不是"必须占一块内存"**；MMIO 不受这条影响：地址是硬编码的，编译器无处可藏。

## 六、补齐边界：volatile 不管的那两件事

- **原子性**：短到不必犹豫的做法是进临界区（根据参与者选择：任务间可用互斥，任务与 ISR 用能覆盖该 ISR 优先级的短临界区，SMP 需跨核锁或原子协议；挂起调度不会禁用中断），长一点用"只置位、只清位"的标志协议；外设侧则优先挑天生原子的入口：`BSRR` 写 1 有效、写 0 无影响，压根不需要读-改-写（[S3 GPIO](../stm32/03-gpio.md)）。GCC 的 `__atomic_*` 内建与 C11 `<stdatomic.h>` 在多核场景（[P4 中断与双核](../esp32/04-irq-dualcore.md)）才真正登场。
- **顺序性**：两条 volatile 访存之间插屏障，才是"配置 A 之后才能碰 B"的可靠保证。别以为"访存都保了，顺序自然对"。第五节 F 行就是反例：漏了宏上的 volatile，`RCC_AHB1ENR` 的写直接排到了 `GPIOF_MODER` 的读后面。反过来，即使 volatile 把两次访问都保成真实访存，编译器仍可能在**它们之间**重排你代码里的其他计算，而总线上的先后也不等于硬件看到的先后（带 prefetch / 写缓冲 / cache 的核尤其如此）。Cortex-M 侧是 `DMB/DSB`（CMSIS-Core 封成 `__DMB()/__DSB()/__ISB()`，定义在 CMSIS 核心头，本项目 ref 未入库，以你手上的版本为准）；带 prefetch 与数据 cache 的核还要处理"读到的不是总线上最新的那一份"：那是下一节的 cache 话题。
- **多执行流可见 ≠ 多执行流正确**：volatile 让双方都真的读写内存，剩下的正确性由上面的机制负责。这条界限画不清，就会得到"加了 volatile 还是偶发出错"的经典悬案。

## 附录：工程完整源码

取证工程（宿主 gcc 与 Cortex-M4 交叉各一套，30 秒可复现）：

<<< ../../code/c/03-volatile/opt_probe.c

构建与取证命令：

<<< ../../code/c/03-volatile/Makefile

六个 `00-blink` 变体的生成脚本（第五节那张表由它跑出来）：

<<< ../../code/c/03-volatile/blink-variants.sh

板级对照工程（第五节逐行过的就是它）：

<<< ../../code/stm32/00-blink/main.c

## 记忆锚点

::: tip 一句话记住
**编译器只对你的"内存值"负责，不对你的"总线动作"负责——`volatile` 就是把总线动作写进合同的那句话。**
登门（访存）它保；排队（原子）、先后（顺序）它不管。
:::

**延伸**：volatile 与寄存器操作（[S3](../stm32/03-gpio.md)）直接相关；原子操作需中断保护（[S4](../stm32/04-nvic-exti.md)）或 RTOS 临界区（[F5](../rtos/freertos/05-sem-mutex.md)）；UB 与 MISRA 规范见 [C7](07-ub-misra.md)。

## 实物实验

本章没有独立实验编号，用两个现成工程做对照，结果记进你的实测笔记：

- **无板上（本机已全部实测通过）**：`cd code/c/03-volatile`，宿主侧 `gcc -std=c11 -Wall -Wextra -O2 -S -o opt_probe.O2.s opt_probe.c`，交叉侧 `make asm-arm` 或 `sh blink-variants.sh`。把 `poll_plain` / `poll_volatile` 两段与六变体表里 C、F、E 三行的 `main` 抄进实测记录，注明编译器版本与完整命令行；
- **板上（三步，编译期结论已核实，肉眼现象待回填）**：`code/stm32/00-blink` 的 `CFLAGS` 由 `-O0` 改 `-O2`：
  1. 什么都不删，直接烧：灯**照闪**。`-O2` 不是潘多拉魔盒，这份代码的两道防线（宏 `volatile` + `asm volatile ("nop")`）都还在；
  2. 把 `main.c:39` 的 `volatile` 与 `main.c:42` 的 `__asm__ volatile ("nop");` **一起**去掉再烧：红灯不再闪（延时整个消失，两条 `BSRR` 写相邻）。只去掉前者对应 B 行，灯照闪，**这是流传最广的一个错误说法，别照抄**；
  3. 想看到 F 行那种"更阴"的现象：把 `main.c:26-34` 六个宏的 `volatile` 去掉（`delay` 不动），灯的行为可能依旧正常（顺序倒了但硬件宽容），也可能配不出模式，**换优化档/换芯片就会变**，这正是要写进合同而不能靠运气的理由。

观测点：肉眼 + 示波器看 PF6（C 行应看到 PF6 恒定或极窄脉冲，而非 1Hz 方波）。

预期现象：差异只随"优化档 × 三处 volatile 有无"变化，其余不变。

::: warning 本轮取证状态
上述六个变体的**编译期**结果已用 `arm-none-eabi-gcc 15.2.1`（`-mcpu=cortex-m4 -mthumb`）在本机全部实测（`code/c/03-volatile/README.md` 附命令与反汇编）；**板上肉眼现象本轮未跑**：写这一版时手边没有接上 F407 与 ST-Link。谁先跑通，欢迎把波形/现象回填到这一节。
:::

## 常见坑

1. **`-O0` 一切正常，发布档翻车**：成因基本就是现场 1/2/3。纪律：**功能验证至少跑一遍与发布一致的 `-O` 档**；出问题先用同档复现，别在 `-O0` 上找 bug。（出现频率第一。）
2. **照抄"去掉 `delay` 的 volatile，`-O2` 灯就不闪"**：本站第一版也这么写，实测才发现不成立：`00-blink` 的循环体里有 `__asm__ volatile ("nop")` 独立兜底，去掉参数 `volatile` 灯照闪（第五节 B 行）。**结论要自己跑一遍才敢写**，包括本站写的结论。
3. **漏了寄存器宏的 volatile，却去查 `delay`**：宏漏词的现象是"顺序倒了 / 换档换芯片才复发"（F、E 行），比"灯不闪"隐蔽得多。自查只要一条命令，把宏展开后再数：`arm-none-eabi-gcc -mcpu=cortex-m4 -E main.c | grep -c 'volatile uint32_t'`。`00-blink` 现状是 9，只漏寄存器宏是 1，三处全漏是 0。**数的是展开结果，不是源文件行数**：宏里的 volatile 写在头文件里，源码 grep 看不全。
4. **自己封装寄存器宏漏了 volatile**：少一个词就进现场 3 与 F 行。优先用 CMSIS 的 `TypeDef` 结构体（`__IO` 一次声明全体生效），别手搓一串地址宏。
5. **拿 `volatile` 当锁**：现场 4。中断与主循环都做读-改-写时必须进临界区，或改用外设侧的原子入口：`BSRR` 写 1 有效、写 0 无影响，天生不需要读-改-写。
6. **过度 volatile 焦虑症**：大缓冲区、纯本地中间变量全标 volatile，`memcpy` 被拆成逐字节访存，性能白送。判据回到第四节那句："谁会绕过编译器改这块内存？"
7. **以为 volatile 能管 cache**：F407（Cortex-M4，无数据 cache）上 volatile + 屏障基本够用；ESP32-S3 有数据 cache，DMA 共享缓冲还要 cache 清理/无效化，光 volatile 会读到旧数据。见 [P6](../esp32/06-spi-i2c-driver.md)、[P10](../esp32/10-flash-nvs-ota.md)。

## 短自测

**1. `while (!(USART1->SR & USART_SR_RXNE));` 还需要另外加 `volatile` 吗？如果 `SR` 字段本身已经带 volatile。**

<details><summary>答案</summary>

不用。CMSIS 的 `USART_TypeDef` 字段自带 volatile 限定（与上面 `GPIO_TypeDef` 同一套写法），`USART1->SR` 这个读已经是真访存。再套一层只会多出不必要的访存，SPL 的 `I2C_GetFlagStatus` 里那两个 `__IO` 局部变量就是"可加而不必加"的活样本（第四节）。

</details>

**2. 为什么 `delay_plain()` 会被优化成一条 `ret`？标准哪一条给了编译器这个权利？**

<details><summary>答案</summary>

两层：① 没有副作用的空循环，标准允许编译器假定它不会无限执行（C11 起按未定义处理），循环可以直接消失；② 计数变量若非 volatile，其值在循环内"没人能改"，比较结果可被缓存与折叠。加 `volatile` 后每次使用都必须真实访存，循环每圈都要读改写它，删不掉。

</details>

**3. 主循环 `flag ^= 1;`、中断里 `flag = 0;`，`flag` 已是 `volatile`。安全吗？为什么？**

<details><summary>答案</summary>

不安全。volatile 只保证"读—改—写"三步都真的对内存发生，不保证三步之间不被抢占：主循环读旧值后被中断打断，中断写 0，主循环回到"写"这步把基于旧值算出的结果写回去，中断的更新就丢了。要么进临界区做读-改-写，要么改成"只置位/只清位"的标志协议，要么用外设侧原子寄存器。

</details>

**4. `volatile uint32_t buf[256]` 当 DMA 缓冲用，代价是什么？F407 与 ESP32-S3 的结论一样吗？**

<details><summary>答案</summary>

代价：对数组的每次普通访问都被强制成真实访存，`memcpy` 之类无法做块搬运优化，性能明显下降。结论不一样：F407 的 Cortex-M4 没有数据 cache，volatile + 屏障基本够；ESP32-S3 有数据 cache，DMA 与 CPU 共享的缓冲还要 cache 清理/无效化，光 volatile 不够。

</details>

<QuizBank chapter="c03-volatile" />

## 对照表：本章概念 → 仓库落点

| 概念 | 仓库落点 |
|---|---|
| 四个现场的完整源码 | `code/c/03-volatile/opt_probe.c`（本附录全文内嵌） |
| 轮询被缓存 | 同上 `poll_plain` / `poll_volatile`，正文第二节汇编引证 |
| 空循环被删 | 同上 `delay_plain`，对照 `code/stm32/00-blink/main.c:39-44` |
| 写被合并 | 同上 `cfg_plain` / `cfg_volatile`，对照 CMSIS `stm32f407xx.h:526-537` |
| 读-改-写非原子 | 同上 `isr_toggle`；外设侧原子入口见 `docs/stm32/03-gpio.md` 的 BSRR 小节 |
| 访存**顺序**被重排 | `code/c/03-volatile/blink-variants.sh` 的 F 行：宏漏 volatile → 读 `GPIOF_MODER` 排到写 `RCC_AHB1ENR` 之前 |
| 外设写被当死 store 全删 | 同上 E 行：三处 volatile 全去 → `main` 只剩一条 `b.n 0` |
| `asm volatile` 是另一道独立防线 | `code/stm32/00-blink/main.c:42`，对照 B 行（只去参数 volatile → 灯照闪）与 C 行（连 `nop` 一起去掉 → 延时消失） |
| "可加而不必加"的 volatile | `stm32f4xx_i2c.c:1261-1264`（第四节），库解剖见 `docs/stm32/15-spl-anatomy.md` |
| 默认 `-O0` 的板级工程 | `code/stm32/00-blink/Makefile:20` |

## 延伸阅读

本章的结论有两份原文可查：

- **[\[D7\]](../reference/bibliography.md#papers)** Eide & Regehr 2008 — 13 款编译器对 volatile 的错编实测，以及"把 volatile 访问包进函数"的对策；本章六变体表的学术版。
- **[\[C1\]](../reference/bibliography.md#toolchain)** N1570 §5.1.2.3 — as-if 规则与"volatile 访问是可观察行为"的原文，本章结论的法律条文。

## 你做到了

- 会取证：能给任意驱动代码生成 `-O0/-O2` 两份汇编，指出被缓存、被删、被合并的访存；
- 会判断：拿到一个 `volatile`，能说清它保的是哪类风险，答不出来源就知道是性能税；
- 会补齐：知道 volatile 不管原子与顺序，临界区、BSRR 式原子寄存器、屏障与 cache 操作各有其岗。

回到开场那段一开优化就死等的轮询：编译器按 as-if 规则办事，被它删掉的每一次读取，在它自己的账本上都是「结果没变」。现在你能把死等现场翻成两份汇编对齐着看，指出哪一条本该读而没读；也能在动 volatile 之前先问一句：这份合同到底要保哪类风险。

<div class="achievement">
✅ 下一站：<a href="04-struct-abi.html">C4 结构体与 ABI</a>：GPIO_TypeDef 凭什么用一个结构体罩住整组寄存器，字段顺序写错会撞到谁的地址。
</div>

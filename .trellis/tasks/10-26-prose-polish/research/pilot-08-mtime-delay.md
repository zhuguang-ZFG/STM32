---
title: V3 MTIME 与裸机延时
status: done
difficulty: 2
minutes: 45
---

# V3 MTIME 与裸机延时

> 🎯 S5 给了 Cortex-M 一颗 24 位"倒数秒表"：写 LOAD、看 COUNTFLAG、硬件自动重装。RISC-V 换成一块 64 位"顺数电表"：mtime 从不回绕、没有归零标志，想定时就自己拿 mtimecmp 比个数，比较到了，MTIP 中断走 [V1](06-clic-irq.md) 的 ECLIC 上门。还有笔反直觉的账：这块表按主频的四分之一走，108MHz 的芯，1ms 只有 27000 格。

## 本章精髓

1. **mtime/mtimecmp 是内存映射，不是 CSR**（Bumblebee 手册 §2.13 原文明说）：64 位顺数、mtime 不小于 mtimecmp 即产生定时器中断（ECLIC 编号 `CLIC_INT_TMR = 7`，gd32vf103.h:102）。SysTick 的四件套（CTRL/LOAD/VAL/CALIB）在这换成"两张内存表 + 一个比较"。
2. **驱动链三步走，主频除以四**：mtime_toggle_a 每个边沿加 1（手册 §3.1）；GD32VF103 的 rtc_clk = core_clk_aon/4（§3.1 注记）；core_clk_aon 与 core_clk 同源同频（§2.1）。三步连起来：**mtime 自增频率 = SystemCoreClock/4**。108M 档 27MHz、1ms = 27000 tick；[V1](06-clic-irq.md) 遗留的"待核验"在此收案。
3. **64 位是福气也是机关**：回绕要 2.2 万年，"防回绕"的担心可以退休；但 RV32 读它必须"高-低-高"循环防撕裂、写 mtimecmp 必须"先高后低"防假中断；周期 tick 没有"自动重装"：ISR 里 `mtimecmp += 周期`，忘了就只响一次。

## 怎么读这一章

- **读过 [S5 SysTick](../stm32/05-systick.md)**：每节先看对照表。"倒数秒表"换"顺数电表"，S5 的减一魔咒和读清魔咒在这全部消失，取而代之的是两条 64 位读写纪律。
- **没读过 S5**：先把"查询式延时 = 读起点、算差值、无符号比较"的骨架记住，本章照此展开。
- [V1 第六节](06-clic-irq.md)已给 MTIME 的结构速览；本章补上地址机关、延时公式与 tick 续约。RTOS 篇把 tick 落在 mtimecmp 上时，用的就是本章第五节。

## 学习目标

- 复述 mtime/mtimecmp 的四个"不是"：不是 CSR、不是倒数、不是 24 位、没有自动重装。
- 引用手册三节推导 mtime 自增频率，算出 108M/72M 档的 1ms tick 数。
- 写出防撕裂的 64 位读法与防假中断的 mtimecmp 写法，各讲出时序依据。
- 用 64 位无符号减法写出查询式 delay_ms，并解释为什么延时常数必须跟着 SystemCoreClock 走。
- 写出周期 tick 的 ISR 续约语句，说出它与 S5"写一次 LOAD 一劳永逸"的本质区别。

## 先修

- [V0 RISC-V 工具链与启动文件](05-riscv-toolchain.md)（SystemInit 与 108M 档）；
- [S5 SysTick：内核的心跳](../stm32/05-systick.md)（周期 = LOAD+1、COUNTFLAG 读清、回绕安全写法，本章的对照锚点）。

## 先跑起来（10 分钟 quick win）

延时公式不必上板才信，宿主 gcc 五分钟先算一遍：

```c
#include <stdint.h>
#include <stdio.h>

int main(void)
{
    uint64_t ticks_per_ms = 108000000ULL / 4U / 1000U;  /* mtime = 主频/4 */
    uint64_t t0 = 0x00000000FFFFFFFFULL;                /* 造一个"低位即将进位"的时刻 */
    uint64_t t1 = t0 + 3 * ticks_per_ms;                /* 3ms 后 */
    printf("1ms = %llu ticks, 3ms = %llu ticks\n",
           (unsigned long long)ticks_per_ms,
           (unsigned long long)(t1 - t0));
    return 0;
}
```

`gcc demo.c -o demo && ./demo` 输出 `1ms = 27000 ticks, 3ms = 81000 ticks`。先减再比的无符号差值跨过 32 位边界也不出错。本章全部延时数学都能这样在宿主预演。

## 动画：MTIME 64 位读写纪律

RV32 读 64 位 mtime 走"高-低-高"循环防撕裂，写 mtimecmp 必须"先高后低"防假中断。两条读写纪律保住跨 32 位边界的时间账。

![MTIME 64 位读写纪律：hi-lo-hi 防撕裂](/anim/riscv-mtime-tick.svg)

## 小节结构

| 小节 | 内容 |
|---|---|
| 一、从秒表到电表 | SysTick 四件套 vs mtime/mtimecmp 两张表；地址机关 |
| 二、主频除四 | mtime_toggle_a/rtc_clk/core_clk_aon 三步链条与 27MHz 账 |
| 三、64 位读写纪律 | 高-低-高防撕裂、先高后低防假中断、非 CSR |
| 四、查询式延时 | delay_ms 的完整实现与分辨率账 |
| 五、周期 tick | MTIP 走 ECLIC 编号 7；ISR 里 mtimecmp 加周期续约 |

## 一、从秒表到电表：SysTick 的四件套换成两张表

先把 [S5](../stm32/05-systick.md) 的旧账和新表摆在一起：

| | SysTick（S5，Cortex-M） | MTIME（本章，Bumblebee） |
|---|---|---|
| 方向/位数 | 24 位倒数 | **64 位顺数** |
| 寄存器 | CTRL/LOAD/VAL/CALIB 四个 | **mtime、mtimecmp 两张内存表** |
| 位置 | SCS 区 0xE000E010（CMSIS core_cm4.h） | 内核私有 TIMER 单元，内存映射——gd32vf103.h 里**没有**它的宏 |
| 周期 | LOAD+1，写一次自动重装 | **无重装**：mtime 不小于 mtimecmp 即中断，之后软件续约 |
| 标志 | COUNTFLAG（读过自清） | 无标志，比大小 |
| 中断号 | IRQn=-1（内核异常） | ECLIC `CLIC_INT_TMR = 7`（gd32vf103.h:102） |
| 使能 | CTRL.ENABLE | 没有 CTRL——想停表只能动 CSR mcountinhibit |

最后一行值得停一拍：**mtime 连"开关"都没有**。上电就顺数，能停它的只有 CSR `mcountinhibit`（手册 §2.13.2，位定义待 ISA 手册核验）；但"不产生中断"你说了算：mtimecmp 挂得足够高，MTIP 永远安静。

地址机关：RISC-V 架构不定义 mtime/mtimecmp 的地址（手册 §2.13 明说"由实现定义"），它们在 GD32VF103 上落在内核私有 **TIMER 单元**，官方固件库驱动 `n200_timer.h` 给出实证：`TIMER_CTRL_ADDR = 0xD1000000`，mtime 偏移 +0x0、mtimecmp 偏移 +0x8（64 位各占 8 字节，n200_timer.h:24-30；n200_func.c:61-69 的 `mtime_lo()/mtime_hi()` 直接按此地址读写）。注意这不是 RISC-V 规范里 QEMU 惯例的 0x0200_0000 布局，**以本芯片官方库为准**。工程里自己写宏：

```c
#define CLINT_BASE      0xD1000000UL             /* GD32VF103 TIMER 域（官方库 n200_timer.h 实证） */
#define MTIMECMP_LO     (*(volatile uint32_t *)(CLINT_BASE + 0x8U))
#define MTIMECMP_HI     (*(volatile uint32_t *)(CLINT_BASE + 0xCU))
#define MTIME_LO        (*(volatile uint32_t *)(CLINT_BASE + 0x0U))
#define MTIME_HI        (*(volatile uint32_t *)(CLINT_BASE + 0x4U))
```

拆成 32 位两半不是多此一举：RV32 的访存指令一次只有 32 位，第三节会讲拆法里的讲究。

## 二、主频除四：mtime 的驱动链

mtime 不是拿内核时钟直接数的。手册给了一条三步链条，每步都有原文背书：

1. **mtime_toggle_a 双边沿触发**：TIMER 单元由 SoC 送来的脉冲信号驱动，"上升沿和下降沿都采样，检测到任何边沿就触发 mtime 加 1"（手册 §3.1 表 3-1）；
2. **GD32VF103 的 rtc_clk**：手册 §3.1 注记写明，"GD32VF103 中 rtc_clk 的频率是 core_clk_aon 的四分之一"，因此 mtime 自增频率 = core_clk_aon/4；
3. **core_clk_aon 就是内核时钟**：手册 §2.1 说，"core_clk 与 core_clk_aon 频率相同、相位相同、来自同一时钟源"，后者只是"常开"分支（睡着了表也走）。

三步连乘：**mtime 自增频率 = core_clk/4 = SystemCoreClock/4**。108M 档 = 27MHz，一个 tick 约 37ns；72M 档 = 18MHz。[V1](06-clic-irq.md) 第六节留的"core_clk_aon 与核心时钟关系待 UM 核验"到此收案，答案在手册 §2.1 的第一句。

两笔衍生账：

- **分辨率账**：1ms = 27000 tick；延时的粒度上限是 1 tick（约 37ns），比 CPU 周期（9.3ns）粗四倍。mtime 管 ms 级"宏观时间"，单周期级标定请用 mcycle/minstret（手册 §2.12）或外设定时器。
- **回绕账**：64 位表有 2 的 64 次方格，按 27MHz 数完一圈要约 2.2 万年。S5 里 uint32_t"49 天必爆"的担心，在 mtime 上以"两万年都不爆"的形态退休。

调试课代表还要知道一条：**调试器指定程序执行期间 mtime 自动停走**（手册 §2.13.1）。本意是不让调试程序污染计时，副作用是断点、单步期间的时间读数不可信，延时标定要脱机跑。

## 三、64 位读写纪律：撕不烂、打不响

**读：高-低-高循环**。mtime_lo 从 0xFFFFFFFF 进到 0x00000000 的那一拍，mtime_hi 同时加 1。若先读高位再读低位，低位可能已经是"新一轮"的，旧高配新低，读数差出一个 2 的 32 次方。纪律是读两次高位当证人：

```c
uint64_t mtime_read(void)
{
    uint32_t hi, lo;
    do {
        hi = MTIME_HI;
        lo = MTIME_LO;
    } while (hi != MTIME_HI);   /* 高位没变 = 低位没跨过 32 位边界 */
    return ((uint64_t)hi << 32) | lo;
}
```

为什么这样就安全：高位不变恰说明这期间没有发生 2 的 32 次方进位，低位的读取落在同一段"高位纪元"里，拼起来必是真值。

**写：先高后低**。把 deadline 往后推（新比较值比当前大）时，必须先写 MTIMECMP_HI 再写 MTIMECMP_LO。反过来先写低位：新低配旧高，若旧高小于 mtime 当前高位，拼出的"半新半旧"值可能瞬间满足"mtime 不小于 mtimecmp"，假 MTIP 当场到账。先写高位把比较值推上高空，中途怎么比都撞不响，最后写低位让它落位。

**非 CSR 再钉一遍**：mtime/mtimecmp 用 `lw/sw` 普通访存读写，`csrr/csrw` 会触发非法指令异常。手册 §2.13 原文："not CSR registers, but Memory Address Mapped system registers"（[V1 坑 3](06-clic-irq.md) 的实操版）。

## 四、查询式延时：S5 的骨架换 64 位心脏

```c
extern uint32_t SystemCoreClock;   /* system_gd32vf103.c 的账本（[V2](07-rcu-108m.md)） */

void delay_ms(uint32_t ms)
{
    uint64_t start = mtime_read();
    uint64_t ticks = (uint64_t)ms * (SystemCoreClock / 4U / 1000U);
    while ((mtime_read() - start) < ticks) {
        /* 先减再比：64 位无符号差值，跨"低位边界"也不出错 */
    }
}
```

三个要点，条条对着 S5 的旧账：

1. **先减再比**。S5 第五节的回绕安全写法在 64 位上更是天经地义；宿主 quick win 里 0xFFFFFFFF 起点那笔账就是证明。
2. **ticks 现算不写死**。SystemCoreClock/4 跟着档位走：108M 档 27000，换 72M 档自动变 18000。写死 27000 的延时，换个档全慢 1.5 倍。
3. **S5 的两个魔咒在这消失**。没有"减一"（比较语义没有 off-by-one，27000 就是 27000）；没有"读清"（查询的是计数本身，不是读过就没的标志）。COUNTFLAG 那个"调试器偷看一眼就死等"的坑，结构性不存在。

分辨率提示：函数调用加两次 mtime_read 本身就有百余 ns 级开销，delay_us 若要精到个位数微秒，请换外设定时器（后续实验篇）；mtime 的主场是 ms 级以上的宏观时间。

## 五、周期 tick：没有自动重装，软件续约

想要 1ms 周期心跳（RTOS tick、毫秒时基），先把比较值挂上：

```c
#define TICK_MS  1U

static uint64_t mtimecmp_read(void)   /* 与 mtime_read 同款纪律 */
{
    uint32_t hi, lo;
    do { hi = MTIMECMP_HI; lo = MTIMECMP_LO; } while (hi != MTIMECMP_HI);
    return ((uint64_t)hi << 32) | lo;
}

void tick_init(void)
{
    uint64_t cmp = mtime_read() + TICK_MS * (SystemCoreClock / 4U / 1000U);
    MTIMECMP_HI = (uint32_t)(cmp >> 32);   /* 先高后低（第三节纪律） */
    MTIMECMP_LO = (uint32_t)cmp;
    /* ECLIC 侧三动作：clicintie[7] 使能、clicintctl[7] 设 level/priority、
       clicintattr[7] 配向量模式——见 [V1 第七节](06-clic-irq.md)，偏移已实证（n200_eclic.h） */
}

void mtime_isr(void)                   /* MTIP → ECLIC 编号 7 分发 */
{
    uint64_t cmp = mtimecmp_read();
    cmp += TICK_MS * (SystemCoreClock / 4U / 1000U);   /* 续约：加周期，不是 now 加周期 */
    MTIMECMP_HI = (uint32_t)(cmp >> 32);
    MTIMECMP_LO = (uint32_t)cmp;
    g_tick++;                          /* 全站毫秒时基；volatile 见 C3 */
}
```

续约那一行是 RISC-V tick 的灵魂，两个对比记牢：

- **对比 SysTick**：S5 写一次 LOAD 硬件自动重装；mtimecmp 到点只响不重置，**不写 `cmp += 周期` 就只响一次**。这是 RISC-V RTOS port 必须处理的第一差异（F8 篇的伏笔）。
- **对比 now 加周期**：`cmp = mtime_read() + 周期` 看着等价，实则每次把"中断延迟"都吃进下一拍，长期走时越走越慢。`cmp += 周期` 把节拍锚在绝对时间轴上。S5 第三节"忘减一相位漂移"的教训在这换了马甲：**写 LOAD 忘减一，tick 慢几 ppm；续约用 now 加周期，tick 慢的是每次中断延迟之和**。RTOS 心跳，认准加法续约。

## 记忆锚点

::: tip 一句话记住
**电表不是秒表：64 位顺数、比大小发中断、非 CSR；主频除四走（108M 档 1ms=27000）；读高-低-高、写先高后低；周期全靠软件续约：cmp 加周期，别用 now 加周期。**
:::

## 实物实验

- **频率标定**：裸机循环里连续 mtime_read() 取差值，反推自增频率。108M 档应约 27MHz、72M 档约 18MHz；与 [V2](07-rcu-108m.md) 的换档实验联动做。
- **delay 对账**：delay_ms(500) 翻转 LED（[V4](09-gpio-minimal.md) 把这个闭环拼完整），逻辑分析仪量周期，误差应在整 tick 范围内。
- **调试器盲区**：断点下读两次 mtime 差值，对比脱机跑的同款数据，手册 §2.13.1 的"调试停走"亲手复现，从此不在调试会话里标定延时。
- **撕裂复现（选做）**：把 mtime_read 换成"只读低位"跑长延时，观察进位时刻的读数跳变。再换回高-低-高循环，症状消失。

## 常见坑

1. **csrr 读 mtime**：不是 CSR（手册 §2.13 原文），非法指令异常。用 lw/sw 走普通访存。
2. **一条 `volatile uint64_t` 直读**：RV32 编译器拆成两次 32 位读，跨越低位进位时高低位撕裂，读到"过去"或"未来"；高-低-高循环是唯一安全读法。
3. **mtimecmp 先写低位**：半新半旧的比较值可能被 mtime 追平，假 MTIP 立刻上门；推 deadline 永远先写高 32 位。
4. **SysTick 肌肉记忆找"归零标志"、等"自动重装"**：mtime 两样都没有。tick ISR 忘写 `cmp += 周期` 就只响一次，RTOS 起不来。
5. **延时常数写死 27000**：换 72M 档后 mtime 是 18MHz，全慢 1.5 倍；用 SystemCoreClock/4 现算，让档位变化自动跟随。

## 短自测

**1. 108M 与 72M 档下，1ms 各对应多少个 mtime tick？写出推导。**

<details><summary>看答案</summary>

mtime 自增频率 = SystemCoreClock/4（驱动链：mtime_toggle_a 双边沿触发、GD32VF103 的 rtc_clk = core_clk_aon/4、core_clk_aon 与 core_clk 同源同频，见手册 §3.1 与 §2.1）。108M 档：108000000/4/1000 = 27000；72M 档：18000。没有"减一"，比较语义没有 off-by-one，算出多少就是多少。

</details>

**2. 为什么 mtime 必须按"高-低-高"循环读？直接声明成 64 位变量一次读会怎样？**

<details><summary>看答案</summary>

mtime_lo 进位回 0 的那一拍，mtime_hi 加 1。RV32 一次访存只有 32 位，64 位读取必然拆两次：若先读高后读低，低位可能已是"新一轮"，旧高配新低，值差出一个 2 的 32 次方量级。高-低-高循环用"第二次读高位未变"证明这期间没发生进位，低位的读取属于同一"高位纪元"，拼出来必为真值。

</details>

**3. 把 deadline 从 t 推到 t+3ms，mtimecmp 先写哪半字？反着写有什么后果？**

<details><summary>看答案</summary>

先写高 32 位再写低 32 位。反着写：新低位配旧高位，若旧高位小于 mtime 当前高位，拼出的比较值可能瞬间被 mtime 追平，假 MTIP 立刻触发。先写高位把比较值推上高空，中途任何比较都撞不响，写完低位才落位到目标。

</details>

**4. mtime 的周期中断重装谁负责？与 S5 写一次 LOAD 有什么本质不同？RTOS tick 的 ISR 必须写哪条语句？**

<details><summary>看答案</summary>

软件负责：mtime 达到 mtimecmp 只触发一次 MTIP，硬件不重置比较值。SysTick 是"写 LOAD 一劳永逸"（硬件自动重装），mtime 是"每次 ISR 续约"。必须写 `mtimecmp += 周期`，不是 `mtime_read() + 周期`（那会把每次中断延迟吃进下一拍，长期走时变慢；加法续约把节拍锚在绝对时间轴上）。

</details>

**5. mtime 自增频率的三步手册链是什么？哪一步把 V1 遗留的"待核验"收了案？**

<details><summary>看答案</summary>

三步：① mtime_toggle_a 上升、下降沿都触发 mtime 加 1（手册 §3.1 表 3-1）；② GD32VF103 的 rtc_clk = core_clk_aon/4，故自增频率 = core_clk_aon/4（§3.1 注记）；③ core_clk_aon 与 core_clk 同源同频（§2.1）。第 ③ 步收了 V1 的案：V1 曾标注"core_clk_aon 与核心时钟的精确关系待 UM 核验"，手册 §2.1 一句"same frequency and phases... same clock source"给出答案。

</details>

## 对照表：本章概念 → 仓库/手册落点

| 概念 | 落点 |
|---|---|
| mtime/mtimecmp 非 CSR、64 位、比较触发 | Bumblebee 手册 §2.13 |
| mtime_toggle_a 双边沿触发 | Bumblebee 手册 §3.1 表 3-1 |
| GD32VF103 rtc_clk = core_clk_aon/4 | Bumblebee 手册 §3.1 注记 |
| core_clk_aon 与 core_clk 同源同频 | Bumblebee 手册 §2.1 |
| 调试器指定程序执行期间 mtime 停走 | Bumblebee 手册 §2.13.1 |
| mcountinhibit 可停表 | Bumblebee 手册 §2.13.2（位定义待 ISA 手册核验） |
| mcycle/minstret 做周期级标定 | Bumblebee 手册 §2.12 |
| CLIC_INT_TMR = 7 | gd32vf103.h:102 |
| mtime/mtimecmp 精确地址（TIMER 域布局） | 官方库实证：0xD1000000（mtime@+0x0、mtimecmp@+0x8，n200_timer.h:24-30）；UM 复核后更新 |
| delay 的 ticks 公式与 27000 | 本章第四节；[V2](07-rcu-108m.md) SystemCoreClock |
| ECLIC 三动作（使能/level/priority/向量） | [V1 第七节](06-clic-irq.md) |
| 回绕安全超时写法（先减再比） | [S5 第五节](../stm32/05-systick.md) |

## 延伸阅读

64 位电表的架构定义：

- **[\[C8\]](../reference/bibliography.md#toolchain)** RISC-V Privileged 20211203 "Machine Timer Registers"一节：mtime/mtimecmp 64 位、从不回绕、"比较到了就置 MTIP"；时钟源不归 ISA 管，所以 1/4 主频那笔账要看 **[\[A14\]](../reference/bibliography.md#chips)** Bumblebee Core Datasheet。

## 你做到了

- 时基换了心脏也会开方：mtime 的驱动链、27MHz 账、读写纪律、续约语句一气呵成；
- S5 的两个魔咒（减一、读清）在 RISC-V 上的"结构性消失"讲得清楚，64 位的两条新纪律（撕裂、假中断）入了肌肉；
- RTOS 篇的 tick 地基打好：mtimecmp 续约那行代码，就是 F8 移植时的第一颗螺丝。

<div class="achievement">
✅ 下一站：<a href="09-gpio-minimal.html">V4 GPIO 最小系统</a>：时钟、时基都齐了，配上 GPIO 点亮第一盏 RISC-V 的灯。
</div>

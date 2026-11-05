---
title: S5 SysTick：内核的心跳
status: done
difficulty: 2
minutes: 30
---

# S5 SysTick：内核的心跳

> 🎯 SysTick 是内核自带的 24 位倒数秒表：归零自动重载、可申请中断——精确延时与 RTOS tick 都靠它。

## 本章精髓

1. 全部家当四个寄存器：**CTRL / LOAD / VAL / CALIB**，基址固定在 0xE000E010（SCS_BASE + 0x0010，`core_cm4.h:1550、1555`）：它是 ARM 内核外设，不是 ST 的，所有 Cortex-M 芯片地址一模一样，这就是 RTOS 移植层敢把它写死的原因。
2. 周期 = LOAD + 1：从 LOAD 数到 0 是 LOAD+1 个节拍，168MHz 下 1ms → `LOAD = 168000 - 1 = 167999`。忘减一不会少数次数，亏的是**相位**：每个 tick 慢 5.95ppm，日漂移 514ms（probe [3] 实测）。
3. COUNTFLAG 读过自清：「读它」这个动作本身有副作用。probe [7] 的对照：单读法 5 个周期数到 5 次，「先偷看再查」双读法数到 0 次，标志被第一次读偷走，查询式延时死等。

- **能理解**：`probe.c` 的 `sim_cycle` 模型（45-64 行）：每个周期 VAL--，**已经为 0** 的那个周期才重载并置 COUNTFLAG；「减一」和「读清」都是这条语义的必然推论，不是口诀。
- **能用**：跑通 42/42 断言；会算任意频率/周期的 LOAD；写出回绕安全的 `(now - then) >= timeout`；说清楚 `SysTick_Config` 干了哪四件事。

## 先修

- [S2 时钟树](02-rcc-clock.md)（168MHz 从哪来）；[S4 NVIC](04-nvic-exti.md)（优先级数值与嵌套规则）；[C3 volatile](../c/03-volatile.md)（`g_tick` 这类共享变量）。

## 先跑起来（10 分钟 quick win）

```bash
cd code/stm32/05-systick
sh probe.sh   # 宿主 gcc 跑 42 条断言；PATH 里有交叉工具链时附送 Cortex-M4 目标文件
```

输出里找这两行：

```text
[宿主] 断言通过 42/42
[6] SysTick_Config(168000)：LOAD=167999 VAL=0 CTRL=0x00000007，SHP[11]=0xF0 → 逻辑优先级 15
```

交叉编译段里再找常数：`movw r2, #16799`、`movw r1, #22783`：167999 与 24 位截断值真的进了目标文件。

出个选择题再跑：要 SysTick 每毫秒敲一次钟，LOAD 里该填原数、原数减一、还是原数加一？跑完看那行 LOAD 等于多少的输出，答案当场揭晓。

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 寄存器版图 | 基址拼接 + 四寄存器偏移（`core_cm4.h:764-770`） | 配置 |
| CTRL 与 COUNTFLAG | 四个位；读清语义与双读法 5:0 对照 | 代码分析 |
| 周期 = LOAD+1 | 167999 推导；忘减一的相位与日漂移 | 配置 |
| 24 位上限 | 0xFFFFFF；100ms 拒配与 737 倍速 bug | 代码分析 |
| 换算与回绕 | ns 整数公式；超时唯一安全写法 | 代码分析 |
| SysTick_Config | 三写寄存器 + 优先级最低的由来（`core_cm4.h:2022-2036`） | 库解析 |

## 一、寄存器版图：四个寄存器，固定在 0xE000E010

CMSIS 原文（`core_cm4.h:764-770`）：

```c
typedef struct
{
  __IOM uint32_t CTRL;   /* Offset: 0x000 (R/W) 控制与状态 */
  __IOM uint32_t LOAD;   /* Offset: 0x004 (R/W) 重载值     */
  __IOM uint32_t VAL;    /* Offset: 0x008 (R/W) 当前值     */
  __IM  uint32_t CALIB;  /* Offset: 0x00C (R/ ) 校准       */
} SysTick_Type;
```

基址是拼出来的：`SCS_BASE = 0xE000E000`（`core_cm4.h:1550`），`SysTick_BASE = SCS_BASE + 0x0010`（`:1555`），得 **0xE000E010**。probe [1] 用 `offsetof` 实测背书：

```text
[1] 布局：CTRL/LOAD/VAL/CALIB 偏移 = 0x0/0x4/0x8/0xC，SysTick_BASE = 0xE000E010（内核外设，所有 Cortex-M 通用）
```

关键认识在最后半句：SCS（System Control Space）是 **ARM 内核的地盘**，不是芯片厂的外设区。STM32、GD32、nRF52 的 SysTick 全在同一个地址，RTOS 的移植层因此只需写一遍 tick 初始化。

## 二、CTRL 四个位：开关、中断、时钟源，和一个「读过就清」的标志

位定义出自 `core_cm4.h:773-783`，`probe.c:36-40` 同义镜像：

| 位 | 名字 | 作用 |
|---|---|---|
| bit0 | ENABLE | 计数器使能 |
| bit1 | TICKINT | 归零时是否申请 SysTick 中断 |
| bit2 | CLKSOURCE | 1 = 内核时钟（168MHz），0 = 参考时钟 |
| bit16 | COUNTFLAG | 归零标志——**读 CTRL 即清 0** |

前三位望文生义；bit16 是本章最实用的坑。硬件语义：VAL 归零那一拍把它置 1；**软件读 CTRL 这个动作本身把它清 0**（read-to-clear，PM0214 的语义，`probe.c:71-77` 的 `sim_read_ctrl` 把它写成了代码）。probe [7] 的对照实验：

```text
[7] COUNTFLAG：周期到后第一次读 CTRL=0x00010005（有标志），紧接第二次读=0x00000005（标志已被上一次读清掉）
    对照：5 个周期里单读法数到 5 次；「先偷看再查」双读法数到 0 次——标志被第一次读偷走，延时死等
```

落到代码（`probe.c:244-260`）：

```c
/* 单读法：读一次，结果直接判断 —— 5 中 5 */
if (sim_read_ctrl(&b) & CTRL_COUNTFLAG) got_right++;
/* 双读法：先偷看一眼（调试打印/无意识的首次读），再查 —— 0 中 */
(void)sim_read_ctrl(&b);
if (sim_read_ctrl(&b) & CTRL_COUNTFLAG) got_wrong++;
```

实战规则：**读一次、存进变量、再判断**。调试器 watch 窗口点一下 `SysTick->CTRL` 都算「偷看」。实物上这个坑表现为延时偶发死等。

## 三、周期 = LOAD + 1：167999 是怎么来的，忘减一亏在哪

先看这张图：倒数、归零重载，和那个"读一次就清"的 COUNTFLAG。

![SysTick 倒数与 COUNTFLAG 读清动画](/anim/systick-tick.svg)

硬件语义（`probe.c:45-48` 注释）：使能后每个周期 VAL--；VAL **已经为 0** 的那个周期执行重载、置 COUNTFLAG。所以从 LOAD 数到 0 再重载，一个完整周期是 LOAD+1 个时钟，「减一」不是口诀，是数出来的。

168MHz 要 1ms：$168000000 / 1000 = 168000$ 个时钟 → `LOAD = 168000 - 1 = 167999`。probe [2] 一族三例：

```text
[2] 168MHz：1ms → LOAD=167999，100us → LOAD=16799，10ms → LOAD=1679999
```

模型实测（`probe.c:128-135`）：LOAD=167999 跑 1680000 周期，归零重载恰好 10 次，周期 = 168000 时钟 = 1.000000ms。

那忘减一（LOAD=168000）会怎样？反直觉的结论：**次数一样，相位不对**。probe [3]：

```text
[3] 模型：LOAD=167999 跑 1680000 周期 → 归零重载 10 次（周期 = LOAD+1 = 168000 周期 = 1.000000ms）
    忘减一：同跑 1680000 周期两者都重载 10 次——差别不在次数在相位；每个 tick 慢 1/168000（5.95ppm），日漂移 514ms
    相位：第 10 次重载——正确配置在第 1512001 个时钟，忘减一在第 1512010 个，9 个间隔共欠 9 个时钟
```

逐拍对账（`probe.c:149-165`）：正确配置第 10 次重载落在第 $1 + 9 \times 168000 = 1512001$ 个时钟；忘减一落在第 $1 + 9 \times 168001 = 1512010$ 个。每个 tick 慢 1/168000 ≈ 5.95ppm，一天欠 $86400000 \times 1000 / 168000 = 514$ ms。短延时根本看不出，长期计时（数据记录器、日历时基）才暴露，这正是「忘减一」阴险的地方。

## 四、24 位上限：LOAD 装不下就是装不下

`core_cm4.h:786-791`：LOAD 与 VAL 的掩码都是 `0x00FFFFFF`，只有低 24 位，`LOAD_MAX = 16777215`。168MHz 下单次最长 $(16777215 + 1) / 168 = 99864$ µs ≈ 99.86ms：1ms tick 无压力，想单次 100ms 就不行。probe [4] 给了两级证据：

```text
[4] 24 位上限：LOAD 最大 16777215（0xFFFFFF）→ 最长单次 99864us（≈99.86ms，1ms tick 无压力，100ms 单次不行）
    请求 100ms（ticks=16800000）：SysTick_Config 返回 1 拒配；若强行 &0xFFFFFF → LOAD=22783，tick 变成 135.6us，ISR 狂跳 737 倍速
```

- **正规路径**：`SysTick_Config` 第一行就是 `(ticks - 1UL) > SysTick_LOAD_RELOAD_Msk` 则返回 1（`core_cm4.h:2024-2027`），即拒配，寄存器一个都没动。所以**必须查返回值**。
- **经典 bug**：不查返回值，强行 `& 0xFFFFFF` 写进去 → `LOAD = 22783`，tick 变成 135.6µs，ISR 以 737 倍速狂跳（$16800000 / 22784 = 737$），系统直接瘫在中断里（`probe.c:176-186`）。

更长的周期怎么办：要么 CLKSOURCE=0 走参考时钟（F407 上是 HCLK/8，单次上限拉到约 800ms），要么换 32 位的 TIM，那是 S6 的地盘。

## 五、时间换算与回绕：超时判断只有一种是安全的

![无符号回绕：先减再比，跨回绕仍正确](/figures/stm32-05-tick-wrap.svg)

1 个时钟 $= 1/168\text{MHz} = 125/21$ ns ≈ 5.952ns。整数公式 `ns = c*1000/168`（向零截断）：c=1 → 5ns，c=168 → 1000ns = 1µs（整 µs 无损），c=1000 → 5952ns = 5.952µs（按整数 µs 取 5µs，丢掉 0.952µs）。probe [5]：

```text
[5] 换算：1 周期 = 125/21 ns ≈ 5.952ns；整数公式 ns=c*1000/168：c=1 → 5ns、c=168 → 1000ns=1us（整 us 无损）、c=1000 → 5952ns=5.952us（按整数 us 取 5us，丢 0.952us）
    回绕：uint32_t ms 计数 49.7 天绕一圈；then=0xFFFFFC18 now=5000 → (now-then)=6000ms（无符号减法跨回绕正确）；而 now>=then+timeout 在 now=2000 时漏报未超时
```

毫秒计数用 uint32_t：$2^{32} / 86400000 \approx 49.7$ 天绕一圈。回绕不是「这辈子遇不到」，是「第 50 天前后必爆」——除非写成**无符号减法**：

```c
uint32_t then = g_tick;                    /* 记录起点 */
if ((uint32_t)(g_tick - then) >= timeout)  /* 先减再比，跨回绕也正确 */
    timeout_handler();
```

反例（`probe.c:205-213`）：`then = 0xFFFFFC18`（绕前 1000ms）、`timeout = 500`，`then + timeout = 4294966796` 没回绕；而 `now = 2000` 已经回绕，朴素写法 `now >= then + timeout` 判出 0（未超时），可真实早已越过 500ms 阈值。这是**漏报**：本该立刻报超时，它却要一直等到 `now` 也爬到 4294966796 才翻转。无符号减法 `(now - then) = 3000 >= 500` 永远正确。全站的 delay、S9 的采样超时、F 篇的事件等待，统一用这个写法。

## 六、SysTick_Config 全貌：三写寄存器，一次设优先级

`core_cm4.h:2022-2036` 全文就六行有效代码：先查上限，然后 **写 LOAD、设优先级、写 VAL、写 CTRL**。probe [6] 实测 `SysTick_Config(168000)` 之后的现场：

```text
[6] SysTick_Config(168000)：LOAD=167999 VAL=0 CTRL=0x00000007，SHP[11]=0xF0 → 逻辑优先级 15（4 位里的最低档，RTOS 就要它在最低）
```

- `CTRL = 0x00000007`：ENABLE | TICKINT | CLKSOURCE 三位全置：内核时钟、开中断、开跑。
- 优先级怎么算的：F407 的 `__NVIC_PRIO_BITS = 4`（`stm32f407xx.h:49`），`SysTick_IRQn = -1`（`:75`）；`__NVIC_SetPriority` 对负数 IRQn 走 `SCB->SHP[((IRQn)&0xF)-4]`（`core_cm4.h:1814-1824`），写入字节 $= priority \ll (8-4)$。$(1 \ll 4) - 1 = 15$，$15 \ll 4 = \text{0xF0}$ → SHP[11] = 0xF0，**4 位优先级里的最低档**。

为什么 RTOS 要它最低：tick 中断里跑的是调度器，而调度必须给一切外设中断让路：串口字节不等人的，高优先级 tick 会把 RXNE 中断顶飞（F3 展开）。

## 附录：工程完整源码

本章取证工程 `code/stm32/05-systick/`（`sh probe.sh` 一条命令跑完，不需要开发板）：

**probe.c**（七个现场：布局 / 周期与相位 / 24 位上限 / 换算回绕 / Config 全貌 / COUNTFLAG 对照）：

<<< ../../code/stm32/05-systick/probe.c

**probe.sh**（宿主编译运行 + 交叉编译取证）：

<<< ../../code/stm32/05-systick/probe.sh

## 记忆锚点

::: tip 一句话记住
**LOAD 定周期、VAL 看进度、CTRL 开关机；频率除千再减一，标志一读就没，超时先减再比。**
:::

**延伸**：SysTick 倒数与 COUNTFLAG 动画见 [S5 动画](/anim/systick-tick.svg)；SysTick 作为 RTOS 时基在 [F0 为什么需要 RTOS](../rtos/freertos/00-why-rtos.md) 展开；GD32 MTIME 对照见 [V3](../gd32/08-mtime-delay.md)。

## 实物实验

- 逻辑分析仪测 PF6 翻转周期：SysTick 版 `delay_ms(500)` 实测 500ms±0.1%，软件延时版误差肉眼可见。同一块板，两种「时间观」的实测对比。
- 双读法坑的实物复现：查询式延时跑到一半，用调试器 watch 窗口点一下 `SysTick->CTRL`，COUNTFLAG 被这次「偷看」清掉，延时再也出不来；再对照读一次存变量的写法，稳过。

## 常见坑

- **忘减一**：`LOAD = 168000` 每 tick 慢 5.95ppm、日漂移 514ms：次数对、相位错，最隐蔽的漂移源（probe [3]）。
- **COUNTFLAG 双读**：调试打印/偷看一次再判断，标志已被偷走，查询式延时死等（probe [7]：5:0 对照）。
- **超上限硬写**：LOAD 超 24 位被 `SysTick_Config` 拒配返回 1；强行截断则 tick 快 737 倍，ISR 打满 CPU（probe [4]）。
- **中断里又调查询式 delay**：ISR 里死等 COUNTFLAG，把 tick 中断自己堵死（嵌套规则回 [S4](04-nvic-exti.md)）。
- **`g_tick` 忘加 volatile**：主循环永远看不到它变（[C3](../c/03-volatile.md) 的经典现场）。

## 短自测

**1. 168MHz 下要 2ms tick，LOAD 写多少？**

<details><summary>看答案</summary>

$168000000 \times 2 / 1000 - 1 = 335999$。周期 = LOAD+1 = 336000 个时钟，整 2.000ms。与 probe [2] 同族：`reload_for_us`（`probe.c:98-102`）就是「频率换算再减一」。

</details>

**2. 为什么「先读一次 CTRL 打印、再读一次判断」的延时会死等？**

<details><summary>看答案</summary>

COUNTFLAG 是 read-to-clear：第一次读（打印那次）已把标志清掉，第二次读永远看到 0。probe [7] 对照：单读法 5 个周期数到 5 次，双读法数到 0 次（`probe.c:244-260`）。正确写法：读一次存进变量再判断。

</details>

**3. `then = 0xFFFFFC18`、`timeout = 500`、`now = 2000`，超时了吗？哪种写法判得对？**

<details><summary>看答案</summary>

超时了：真实已过 3000ms。`(uint32_t)(now - then) = 3000 >= 500` 判对；`now >= then + timeout` 中 `then+timeout = 4294966796` 没回绕、`now = 2000` 已回绕，误判未超时（probe [5] 反例）。只有「先减再比」跨回绕永远正确。

</details>

**4. `SysTick_Config(168000)` 后 CTRL 是什么值？优先级是多少？怎么算的？**

<details><summary>看答案</summary>

`CTRL = 0x00000007`（ENABLE+TICKINT+CLKSOURCE）；`SHP[11] = 0xF0`，逻辑优先级 15，4 位优先级的最低档：$(1 \ll 4) - 1 = 15$，$15 \ll 4 = \text{0xF0}$（`stm32f407xx.h:49`、`core_cm4.h:2030`），probe [6] 实测同值。

</details>

**5. 请求 100ms tick 会发生什么？**

<details><summary>看答案</summary>

ticks = 16800000，`ticks - 1 > 0xFFFFFF`，`SysTick_Config` 返回 1 拒配、寄存器不动（`core_cm4.h:2024-2027`）。不查返回值硬写 `&0xFFFFFF` → LOAD=22783，tick 变 135.6µs、ISR 737 倍速狂跳（probe [4]）。长周期请换 TIM（S6）。

</details>

## 对照表：本章概念 → 仓库落点

| 概念 | 仓库落点 |
|---|---|
| 四寄存器布局与基址 0xE000E010 | `probe.c:25-43`；`core_cm4.h:764-770、1550、1555` |
| CTRL 四个位 | `probe.c:36-40`；`core_cm4.h:773-783` |
| COUNTFLAG 读清与 5:0 对照 | `probe.c:71-77`（sim_read_ctrl）、`232-260` |
| 周期 = LOAD+1、相位差 9clk、日漂移 514ms | `probe.c:45-69`（模型）、`128-165` |
| 24 位上限与 737 倍速 | `probe.c:42`、`167-186`；`core_cm4.h:786-791` |
| ns 换算与回绕安全超时 | `probe.c:188-213` |
| SysTick_Config 三写 + 优先级 15 | `probe.c:79-96`、`216-230`；`core_cm4.h:2022-2036`；`stm32f407xx.h:49、75` |
| 断言总账 42/42 | `probe.c:262-263`；`probe.sh` 第 1 段输出 |

## 你做到了

- 延时从「估」变「算」：167999 不再是魔法数，是「周期 = LOAD+1」的必然；
- 拿到全站反复使用的毫秒时基，回绕安全的超时写法入库；
- RTOS tick 前置课完成。你已经知道它为什么住在内核、为什么优先级必须最低。

押减一的理由这章替你焊死了：差的那一拍不是误差，是计数器从零起跳的规矩。

<div class="achievement">
✅ 下一站：<a href="06-tim.html">S6 定时器 TIM</a>：24 位不够用时，32 位 TIM 登场。从数脉冲到发 PWM，STM32 最全能的外设。
</div>

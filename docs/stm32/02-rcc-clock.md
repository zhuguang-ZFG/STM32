---
title: S2 RCC 时钟树：168MHz 是怎么算出来的
status: done
difficulty: 3
minutes: 40
---

# S2 RCC 时钟树：168MHz 是怎么算出来的

> 🎯 时钟树是 STM32 的"配电网"：发电厂（HSE/HSI）→ 变电站（PLL 倍频）→ 输电线路（AHB/APB 分频）→ 每家每户的电表（外设使能位）。停电排查从电表开始——所以"先时钟、再模式、后数据"是我们的祖训。

## 本章精髓

1. **PLL 公式一行写尽**：`SYSCLK = HSE / M × N / P`。但每个字母都有芯片给的取值范围（RM0090 §7.2.3）：PLLM∈[2,63] 且 VCO 输入必须 1~2MHz。PLLN∈[50,432] 且 VCO 输出必须 100~432MHz。PLLQ∈[2,15] 且必须让 VCO/PLLQ **正好** 48MHz（USB OTG FS 专用）。
2. **分频有连锁反应**：AHB(/1) → APB1(/4)/APB2(/2)。挂在 APB 上的定时器还有一条隐藏规则：**APB 分频 ≠ 1 时定时器时钟 ×2**，所以 84MHz 的 APB1 上，TIM 时钟其实是 84×2=168MHz 的一半……不对，是 42×2=84MHz。这一条在 [S6](06-tim.md) 会用实验实测。
3. **Flash 等得及吗**：168MHz 下 Flash 取指要 5 个等待周期，而且这张表按**供电电压分列**（RM0090 Table 10），不按电压缩放档分列。电压档（VOS）只决定 HCLK 的天花板：VOS='0' 最多 144MHz，VOS='1' 才允许 168MHz。

- **能理解**：为什么 1MHz 是 PLL 的"设计目标值"而不是外设时钟；为什么改完分频要回读 SWS 才算数；为什么把晶振值填错不会报错、只会全盘算错。
- **能用**：给任意 HSE 晶振手算一组合法的 M/N/P/Q；在 `01-rcc-clock` 上电后切到 168MHz 并用 MCO1 量到它。

## 先修

- [S1 架构](01-arch.md)（AHB/APB 归属）；[C4 结构体](../c/04-struct-abi.md)。

## 先跑起来（10 分钟 quick win）

**没有板子也能把本章的账全跑完**。进 `code/stm32/01-rcc-clock`：

```bash
sh probe.sh          # 三步：宿主跑固件自己的函数 → 错宏对照 → 交叉链 -O2 反汇编对账
```

第 1 步把 `RCC_PLLCFGR`/`RCC_CFGR` 两个宏改指一对假寄存器后 `#include "main.c"`，所以断言跑的是固件本体而不是另抄一遍算术：八种晶振的 M/N/P/Q、`0x07405408` 的位段账、等待周期十个边界、时钟树回读解出的 `{168e6, 168e6, 42e6, 84e6, 84e6}`，共几十条断言全绿。第 3 步把 `main.c` 编成 Cortex-M4 的 `-O2` 目标文件，在字面量池里当场挖出同一个 `0x07405408`：**源码算出来的字 == 落到寄存器里的那个字**。

有板子再加一步：构建默认版本（留在 HSI 16MHz，不碰晶振）`make`，GDB 读 `g_clock_tree[]`，你会看到 `{16000000, 16000000, 16000000, 16000000, 16000000}`：芯片一出生就在跑 HSI 16MHz，PLL 还没上岗。这就是"先时钟"的直观证据。这句不用上板也能验：默认版编 `-O2` 后，字面量池里 `0x07405408` 和 PLLON 那个 `#16777216` **都不存在**，对 `#2052`（PLLCFGR）唯一的一次引用是一条 `ldr`：回读函数要读它，但没人写它。

先别急着跑，押个数：默认版固件一行都没碰晶振，芯片一上电跑的会是哪个钟？出厂自带的内部钟，还是外面的晶振？押完再跑，g_clock_tree 那五行数字就是裁判。

## 动画：时钟树的五个闸门

HSE/HSI 两个水源、PLL 这个泵站、SW 这个总闸、AHB/APB 两条输电线，每一段"通了/断了"都有对应的寄存器位。盯紧最下面的"对账"小窗：理论值先算对，上板再用仪器量回来：程序以为的时钟和引脚上量到的时钟必须一致。

![RCC 时钟树动画](/anim/rcc-clock-tree.svg)

## 板卡与版本前提

- **HSE 晶振值未核实**：正文用 8MHz 与 25MHz 两例做手算演示，套用前以你手上板卡的规格书/原理图为准；工程默认 `HSE_VALUE_HZ=8000000`，这个宏改错了程序不会报错，只会全盘算错（见常见坑）。
- 寄存器位定义以 ST 官方 CMSIS 头文件 `cmsis_device_f4`（commit `9192c7b9`）为准；PLL 取值范围与 Flash 等待周期以 RM0090 Rev 18 为准。
- 本机工具链：xPack GNU Arm Embedded GCC 15.2.1 + GNU Make 4.4.1。

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 一、四个时钟源 | HSI/HSE/LSI/LSE 分工与精度对比 | 配置 |
| 二、PLL 手算 | M/N/P/Q 逐段拆解；8MHz 与 25MHz 两例算到底 | 配置 |
| 三、提频六步 | 顺序 + 每步对应的寄存器位 + 回读确认 | 代码分析 |
| 四、总线分频与定时器×2 | HPRE/PPRE 编码；APB 分频≠1 时定时器时钟×2 | 代码分析 |
| 五、Flash 与电压档 | RM0090 Table 10 全表 + VOS 天花板 | 配置 |
| 六、MCO1 实测 | PA8 复用输出 SYSCLK/4，仪器验证 | 引脚 |
| 七、代码分析 | `01-rcc-clock/main.c` 逐段对表 + `probe.sh` 无板取证（固件本体跑断言、`-O2` 反汇编对账） | 代码分析 |
| 八、上游对照 | HAL `OscConfig/ClockConfig` 逐行对照（hal_rcc.c @ 1f6451c）；SPL 一手源码仍缺 | 库解析 |

## 一、四个时钟源：发电厂四种

| 源 | 精度 | 何时用 |
|---|---|---|
| HSI（内部 RC，16MHz） | ±1% 量级 | 复位默认、调试用、没有晶振时兜底 |
| HSE（外部晶振，4~26MHz） | 取决于晶振 | 需要精确波特率/定时时必选 |
| LSI（内部低速 RC，~32kHz） | 差 | 独立看门狗 |
| LSE（外部 32.768kHz 晶振） | 好 | RTC |

复位之后芯片只用 HSI 16MHz。这意味着两件事：第一，什么都不配也能跑（`00-blink` 就是这样）；第二，**只要想用更高的频率，就得亲手走一遍提频流程**。

## 二、PLL 手算：M/N/P/Q 一个都不能猜

![PLL 分频链：M/N/P/Q 各管一段频率](/figures/stm32-02-pll-chain.svg)

公式（RM0090 Rev 18 §7.2.3）：

- `f(VCO) = f(PLL 输入) × PLLN / PLLM`
- `f(SYSCLK) = f(VCO) / PLLP`
- `f(48MHz) = f(VCO) / PLLQ`

约束（同一节的原文）：PLLM∈[2,63]，且必须让 **VCO 输入落在 1~2MHz**（原文推荐 2MHz 以限制抖动）。PLLN∈[50,432]，且 **VCO 输出必须在 100~432MHz**。PLLP 取 /2 或 /4。PLLQ∈[2,15]，且 USB OTG FS 需要正好 48MHz。

**8MHz 晶振、VCO 输入 1MHz（最常见的教程写法）**：

| 参数 | 值 | 怎么来的 |
|---|---|---|
| M | 8 | 8MHz / 8 = 1MHz（VCO 输入） |
| N | 336 | 1MHz × 336 = 336MHz（VCO） |
| P | 2 | 336 / 2 = 168MHz（SYSCLK） |
| Q | 7 | 336 / 7 = 48MHz（USB） |

**8MHz 晶振、VCO 输入 2MHz（RM0090 推荐的低抖动写法）**：M=4、N=168、P=2、Q=7。VCO 仍是 336MHz，SYSCLK 与 USB 结果不变，只是参考输入更干净。

**25MHz 晶振（另一种常见板子）**：M=25 → 1MHz，其余与上面相同。**M 的职责就是把晶振归一化到 1MHz（或 2MHz）**，不是"越大越好"。

> **【注】** 1MHz 这个数只是设计目标，不是规范值。规范给的是 1~2MHz 的窗口；选 1 还是 2 取决于你愿不愿意为了更低的抖动牺牲一点点配置便利。这也回答了"为什么教程里永远是 M=8/N=336"：那不是唯一解，只是最常抄的解。

<ClockCalc />

## 三、提频六步：顺序就是正确性

完整的提频流程，每步都有对应的寄存器位：

1. **电压档**：`PWR_CR.VOS = 1`（bit14，Scale 1，解锁 168MHz）。注意 F405/407 **没有** VOSRDY 就绪位（那是 F42x/43x 的），写入即生效，不存在可等待的硬件回执。
2. **Flash 等待周期**：`FLASH_ACR.LATENCY = 5WS`（[2:0]），并开预取 `PRFTEN`（bit8）。这一步必须在提速之前，否则 CPU 去 Flash 取指会超时跑飞。
3. **开 HSE 并等就绪**：`RCC_CR.HSEON = 1`（bit16），轮询 `HSERDY`（bit17）。晶振虚焊/负载电容不对时 HSERDY 永远不来，**必须带超时回退 HSI**，不能死等。
4. **配 PLL 并启动**：`RCC_PLLCFGR` 写 M/N/P/Q/SRC（M[5:0]、N[14:6]、P[17:16]、SRC[22]、Q[27:24]），然后 `RCC_CR.PLLON = 1`（bit24），轮询 `PLLRDY`（bit25）。
5. **切 SYSCLK**：`RCC_CFGR.SW = 10b`（[1:0]），然后**读 `SWS`（[3:2]）确认硬件真的换了**。写完 SW 不等于已切换。
6. **总线分频**：`RCC_CFGR.HPRE/PPRE1/PPRE2`。AHB=/1，APB1=/4（上限 42MHz），APB2=/2（上限 84MHz）。

> **【注】** RM0090 对 HPRE 有一条容易被忽略的 caution："分频值在写入 HPRE 后的 1~16 个 AHB 周期内才生效"。推论：**升频前先把总线分频降下来**，否则新频率会瞬间喂给一条还是老分频的总线，超过上限一拍就可能跑飞。降频则可以直接做。

![提频六步：先降速，再提速](/anim/rcc-six-gates.svg)

## 四、总线分频与定时器 ×2

AHB 上挂着 CPU、内存、DMA、GPIO；APB1/APB2 上挂着外设。所以"总线分频"不只是数字游戏，它决定每个外设能拿到多快的时钟。

还有一条不在框图里、但在寄存器说明里的规则：**当 APBx 预分频 ≠ 1 时，挂在这条 APB 上的定时器时钟 = PCLK × 2**。这条规则在 [S6](06-tim.md) 会用 `02-tim-pwm` 实测出来：把 APB1 从 /1 切到 /2，PCLK1 减半，但 TIM3 的时钟纹丝不动。

## 五、Flash 与电压档：RM0090 Table 10

等待周期按 **VDD 电压范围** 分列（RM0090 Rev 18 Table 10）：

| VDD | 0WS | 1WS | 2WS | 3WS | 4WS | 5WS | 6WS | 7WS |
|---|---|---|---|---|---|---|---|---|
| 2.7~3.6V | ≤30 | ≤60 | ≤90 | ≤120 | ≤150 | ≤168 | — | — |
| 2.4~2.7V | ≤24 | ≤48 | ≤72 | ≤96 | ≤120 | ≤144 | ≤168 | — |
| 2.1~2.4V | ≤22 | ≤44 | ≤66 | ≤88 | ≤110 | ≤132 | ≤154 | ≤168 |
| 1.8~2.1V（预取关） | ≤20 | ≤40 | ≤60 | ≤80 | ≤100 | ≤120 | ≤140 | ≤160 |

VOS 不在这张表里，它只决定天花板：F405/407 在 VOS='0' 时 fHCLK 上限 144MHz，VOS='1' 时 168MHz。所以"能不能跑 168MHz"是两步检查：先过电压档（VOS=1），再过等待周期（3.3V 下 5WS）。

## 六、MCO1 实测：把内部时钟引出来看

`RCC_CFGR.MCO1PRE`（[26:24]）选一个分频比，把 SYSCLK 送到 PA8（AF0，见 DS8626 Table 9）。/4 之后 168/4=42MHz，正好落在示波器/逻辑分析仪的舒服区间。**量到的数乘 4 就是 SYSCLK**，这是"程序以为"与"硬件实际"之间最短的对账路径。

## 七、代码分析：`01-rcc-clock/main.c`

逐段对表（源文件见工程目录，行号以当前提交为准）：

- `systick_init()`：SysTick 的 LOAD 用 **HCLK** 而不是 APB 时钟，这是延时函数与时钟解耦的第一步。
- `flash_latency_ws_3v3()`：只实现 2.7~3.6V 那一列（开发板常见供电），其余电压范围在注释里给全。
- `flash_config()`：先 VOS 再 LATENCY 再预取；没有"等 VOS 生效"的自旋，因为 F405/407 没有那个就绪位。
- `pll_params_from_hse()`：由晶振频率推 M/N/P/Q，超出合法范围就拒绝，而不是硬凑。
- `clock_init()`：六步顺序逐行对应第三节；HSE 起振带超时，超时回退 HSI 并把 `g_clock_status` 置 1。
- `clock_tree_readback()`：从 CFGR 反推真实时钟树，含"APB 分频≠1 时定时器 ×2"这条隐藏规则。
- `mco1_init()`：把 SYSCLK 引到 PA8；分频编码交给纯函数 `mco1_pre_for()`，好让宿主探针能直接调它。

### `probe.sh`：把这一章的账全部搬到宿主机上跑

手法只有一句：`probe.c` 先把 `RCC_PLLCFGR`/`RCC_CFGR` 两个宏改指到一对 `static uint32_t` 假寄存器，再 `#include "main.c"`（顺带 `#define main firmware_main` 让位给宿主的 `main`）。于是下面这些断言跑的是**固件里那几段函数本体**，不是另抄一遍算术，这也正是"回读算出来的数"这种逻辑唯一能被离线验证的方式。

本机实跑（x86 gcc 16.1.0 + xPack 15.2.1，`sh probe.sh`）：

| 探针小节 | 实跑结论 |
|---|---|
| 1 · `pll_params_from_hse()` | 8/25/16/12/6/4 MHz 六种晶振全部 M=晶振/1MHz、N=336、P=/2、Q=7 → SYSCLK 168000000、USB 48000000；11.0592 MHz 返回 **−2**（除不出整兆），64 MHz 返回 **−1**（M 溢出 6 位） |
| 2 · 位段打包 | `M=8 N=336 P=/2 SRC=HSE Q=7 → 0x07405408`，与 `-O2` 字面量池里 `.word 0x07405408` **同字** |
| 3 · `flash_latency_ws_3v3()` | 16→0、30→0、31→1、60→1、61→2、90→2、120→3、150→4、**151→5**、168→5 WS（每个边界各测两侧） |
| 4 · `clock_tree_readback()` | 喂 `SWS=PLL, PPRE1=0b101, PPRE2=0b100` → `{168000000, 168000000, 42000000, 84000000, 84000000}`；对照组 `PPRE1=/1` → PCLK1=TIM2CLK=168000000，×2 规则不触发 |
| 4b · 表长陷阱 | 旧 16 格表在 `0b100..0b111` 全读成 /1；新 8 格表读出 /2 /4 /8 /16（详见常见坑） |
| 5 · `mco1_pre_for()` | 168MHz → div=4 → `pre=0b110(6)` → PA8=42000000；按 `div−1` 写 `pre=0b011(3)` → div=1 → PA8=168000000，再按 /4 把读数乘回去得 672000000，**凭空多出 504 MHz** |
| 6 · 错宏对照 | `HSE_VALUE_HZ=25000000` 而 `BOARD_HSE_HZ=8000000`：写入 `0x07405419`（M=25）→ 程序以为 168000000、VCO 输入 320000、引脚 53760000、USB 15360000，**差 114240000 Hz，而返回值 = 0** |

`-O2` 反汇编那一段（`build/main_o2.o`，text 944 字节）给出两件事。**提频顺序在指令流里单调向前推进**：`orr #16384`(VOS) → `bic #7 / orr #5 / orr #256`(LATENCY+预取) → `orr #65536`(HSEON) → `lsls #14 / bpl`(等 HSERDY) → `str [r2,#2052]`(PLLCFGR) → `orr #16777216`(PLLON) → `bic #3 / orr #2`(SW) → `and #12 / cmp #8`(读 SWS)——三处等待各自成环（等 HSERDY、等旧 PLL 停、等 SWS），但步骤本身没有一步倒回去。**常量折叠把 M/N/P/Q 压成四个立即数**：`movs r2,#8 / mov.w r3,#336 / movs r2,#2 / movs r3,#7` 直接存进 `g_pll_*`，一条除法都没有。折叠本身是好事，但宏填错时错值同样会被折叠成一个"看起来正常"的立即数，运行时再没有第二双眼睛。

## 八、上游对照：HAL 做同一件事

ST 官方仓库 [`STMicroelectronics/stm32f4xx_hal_driver`](https://github.com/STMicroelectronics/stm32f4xx_hal_driver)（master @ `1f6451c`，2026-10-06 拉取）的 `HAL_RCC_OscConfig()` / `HAL_RCC_ClockConfig()` 做的是同一串动作，逐条对本工程：

| 本工程 `clock_init()` | HAL 对应（hal_rcc.c 行号 @ 1f6451c） | 对照结论 |
|---|---|---|
| HSEON 后轮询 HSERDY，超时回退 HSI | `HAL_RCC_OscConfig()`：轮询 `RCC_FLAG_HSERDY`，`HAL_GetTick` 超时返回 `HAL_TIMEOUT`（L231-259） | 同思路：晶振可能不来，死等是 bug |
| 先 VOS 再 LATENCY 再预取 | `HAL_RCC_ClockConfig()` 只管 LATENCY——写入后**回读校验，不符直接 `HAL_ERROR`**（L613-626）；VOS 归 PWR 模块，F4 写完即生效、无就绪位可等 | 顺序一致；HAL 多一步回读 |
| HPRE/PPRE 直接写目标值 | 切 HPRE 前**先把 PPRE1/PPRE2 打到 /16**（L635-649，注释原文：不经过非规格相位） | 本工程 HPRE 恒 /1 无此窗口；做分频切换时 HAL 更保守 |
| 写完 SW 轮询 SWS 回执 | 同：切 SYSCLK 后轮询 `RCC_CFGR_SWS`（L681） | 一致 |

SPL（StdPeriph）未随 ST 官方 GitHub 分发，本轮仍缺一手源码；其 `SetSysClockTo168M()` 与本节序列同构，位定义以 RM0090 为准。

## 附录：工程完整源码

不用跳 GitHub，整个 `main.c`、离线探针和取证脚本都在下面，滚动即达：

<<< ../../code/stm32/01-rcc-clock/main.c

<<< ../../code/stm32/01-rcc-clock/probe.c

<<< ../../code/stm32/01-rcc-clock/probe.sh

## 记忆锚点

::: tip 一句话记住
**先电压、再等待、后切钟；先降总线、再提主频；写完 SW 要看 SWS；APB 分频不是一，定时器时钟自己乘二。**
:::

**延伸**：RCC 时钟树动画见 [S2 动画](/anim/rcc-clock-tree.svg)；Flash 等待周期与频率的关系在 [B5 map 审计](../build/05-map-size.md) 有体积影响；GD32 RCU 对照见 [G1](../gd32/01-rcu-clock.md)。

## 实物实验

- MCO1 量频：`USE_HSE_PLL=1` 构建后量 PA8，应为 ≈42MHz；换回默认构建应为 ≈4MHz（16/4）。
- 对比实验：`make USE_HSE_PLL=1 HSE_VALUE_HZ=25000000`（如果你的板子是 25MHz 晶振）与 8MHz 版对照，GDB 读 `g_clock_tree[]` 应完全一致。
- 翻车实验（选做）：把 `flash_latency_ws_3v3()` 的返回值硬减 2，跑 168MHz，观察 HardFault，再用 [S16](16-debug-hardfault.md) 的方法读现场。
- 上板实测回填：用示波器实测霸天虎 HSE 晶振频率，回填到正文与工程宏（**待上板实测**）。

## 常见坑

- **MCO1PRE 编码想当然按"分频比 − 1"写**：它是 `0xx=不分频、100=/2、101=/3、110=/4、111=/5`（HAL `RCC_MCODIV_1..5` = 0/4/5/6/7）。按 `div−1` 写，/4 会落到"不分频"区，PA8 吐的是 168MHz，对账结论全部作废。
- **忘配 Flash 等待周期就切 168MHz**：取指超时，直接跑飞。顺序：先 LATENCY，再切 SYSCLK。
- **HSE 起振失败死等**：晶振虚焊/负载电容不对时 HSERDY 永远不来，代码要加超时回退 HSI。
- **改了 PLL 忘更新 SystemCoreClock**：后面的延时/波特率全错，本章工程用 `g_clock_tree[]` 回读，不依赖手工维护的全局变量。
- **HPRE 生效延迟**：写完 HPRE 立刻读分频后的时钟，读到的还是旧值；升频前先把总线分频降下来。
- **把 PLL 的 VCO 输入 1MHz 当外设时钟**：1MHz 是设计目标，不是可以喂给 USART 的时钟（见 [S7](07-usart.md) 的 115200 误差算例）。
- **PPRE 查表照 HPRE 开 16 格**（本章改之前的真 bug，`probe.sh` 第 4b 节实测）：HPRE 是 4 位字段、PPRE 只有 3 位，16 格表用 3 位索引最大只到 7。`/2 /4 /8 /16` 四档全部落在第一格——**APB 分频被静默读成 /1**。症状不是崩溃而是离谱：APB1 被算成 168MHz，再套上"分频≠1 定时器 ×2"，屏幕上会出现 336MHz 这种这颗芯片根本给不出的频率。表长要按字段位宽开，`{1,1,1,1,2,4,8,16}` 八格才对。
- **`HSE_VALUE_HZ` 填错，程序一声不吭**（`probe.sh` 第 2 步实跑）：宏写 25MHz、板上焊 8MHz 时，固件写入 `PLLCFGR` 的是 `M=25 N=336` → `0x07405419`，`pll_params_from_hse()` 返回值 **0**（它只校验宏，不知道板上是什么）。`clock_tree_readback()` 也算出 168000000，而引脚上实际是 53760000 Hz，USB 那一路 15360000 Hz（要 48MHz）。回读只证明"你写的位和你的宏自洽"，不证明晶振为真。要让程序开口，得自己加一步 MCO1 实测对账。

## 短自测

1. 为什么切 168MHz 之前要先配 Flash 等待周期和电压档？
<details><summary>参考答案</summary>Flash 取指在 3.3V 下 150~168MHz 要 5 个等待周期，不配够就取指超时、随机跑飞。电压档 VOS='0' 时 HCLK 上限是 144MHz，不配电压档连 168MHz 的资格都没有。顺序上必须先慢下来（电压档+等待周期）再提速。</details>

2. HSE=8MHz 时给出两组合法的 M/N/P/Q，并说明哪一组更干净。
<details><summary>参考答案</summary>VCO 输入 1MHz：M=8/N=336/P=2/Q=7（SYSCLK 168MHz、USB 48MHz）。VCO 输入 2MHz：M=4/N=168/P=2/Q=7，结果相同。RM0090 推荐 2MHz 输入以限制 PLL 抖动，第二组更干净。</details>

3. HCLK=168MHz、APB1 分频 /4 时，TIM2 的时钟是多少？
<details><summary>参考答案</summary>PCLK1 = 42MHz；APB 分频 ≠ 1 时定时器时钟 ×2 → TIM2 时钟 = 84MHz。只记 42MHz 会把所有定时器算慢一半。</details>

4. 写完 `RCC_CFGR.SW` 立刻读 `SWS`，可能看到什么？该怎么办？
<details><summary>参考答案</summary>可能看到旧值，硬件切换需要时间。正确做法是轮询 SWS 直到它等于你写的 SW，并加超时；读不到回执就当切换失败处理。</details>

5. 宏里写 `HSE_VALUE_HZ = 25000000`、板上实际焊 8MHz。编译不报错、运行也不报错，`clock_tree_readback()` 还回了个 168000000。`probe.sh` 第二步实测这一串的差值和函数返回值是多少？为什么回读救不了你？
<details><summary>参考答案</summary>实测：写入 `PLLCFGR` 的是 `M=25 N=336` → `0x07405419`，程序以为 SYSCLK = 168000000 Hz，引脚上实际 53760000 Hz，差 114240000 Hz。而 `pll_params_from_hse()` 返回值 **0**：它只校验宏本身（VCO 输入落在 1~2MHz 就放行），不知道板上焊的是什么。回读证明的只是"你写的位和你的宏自洽"，晶振真假它管不着。要把这两个数分开，只能靠 MCO1 把内部时钟引到引脚上实测。</details>

6. HPRE 是 4 位字段、PPRE 是 3 位字段。照 HPRE 给 PPRE 开一张 16 格的分频表，会出什么症状？
<details><summary>参考答案</summary>3 位索引最大只到 7，表的后 8 格永远读不到，`/2 /4 /8 /16` 四档全部落在第一格 → APB 分频被静默读成 /1。症状不是崩溃而是离谱：APB1 被算成 168MHz，再套上"分频≠1 定时器 ×2"，屏幕上出现 336MHz 这种这颗芯片根本给不出的频率。所以表长必须按字段位宽开：`{1,1,1,1,2,4,8,16}` 八格。</details>

<QuizBank chapter="s02-rcc-clock" />

## 对照表：本章概念 → 仓库与上游落点

| 概念 | 落点 |
|---|---|
| PLL 取值范围与公式 | RM0090 Rev 18 §7.2.3 RCC_PLLCFGR 说明 |
| Flash 等待周期按电压分列 | RM0090 Rev 18 Table 10 |
| VOS 天花板 | 同章 Note（F405/407 VOS=0 → ≤144MHz） |
| MCO1 = PA8 AF0 | DS8626 Rev 9 Table 9 |
| 提频六步 + 回读确认 | [code/stm32/01-rcc-clock/main.c](https://github.com/zhuguang-ZFG/mcu/blob/main/code/stm32/01-rcc-clock/main.c) `clock_init()` |
| 动画 | [rcc-clock-tree.svg](/anim/rcc-clock-tree.svg) |
| PLLCFGR 那个字（源码 ↔ 反汇编同字对账） | `probe.sh` 第 1 步断言 + 第 3 步 `objdump` 字面量池 `0x07405408` |
| 提频顺序在指令流里单调 | `probe.sh` 第 3 步 `-O2` 反汇编（`orr #16384 → bic #7/orr #5 → orr #65536 → str #2052 → cmp #8`） |
| 常量折叠把 M/N/P/Q 压成立即数 | 同上，`movs r2,#8 / mov.w r3,#336 / movs r2,#2 / movs r3,#7` |
| PPRE 表长按字段位宽（本章修的 bug） | `probe.sh` 第 1 步 第 4b 节新旧表并排 |
| 错宏 `HSE_VALUE_HZ` 静默算错 | `probe.sh` 第 2 步（`BOARD_HSE_HZ` 与宏不一致那一遍，差 114240000 Hz、返回值 0） |
| HAL 同名流程逐行对照 | ST 官方仓库 [stm32f4xx_hal_driver](https://github.com/STMicroelectronics/stm32f4xx_hal_driver) @ `1f6451c` `Src/stm32f4xx_hal_rcc.c`（见 §八）；SPL 未随官方 GitHub 分发，一手源码仍缺 |

## 你做到了

- 时钟树从"一坨框图"变成会算会配的配电网；
- MCO1 实测给了你第一个"把内部信号引出来看"的技能；
- "程序以为"与"硬件实际"之间的对账方法（回读 CFGR / 量 MCO1）从此归你。

那个数 g_clock_tree 报出来了：五行全是出厂内部钟，PLL 还没上岗。从猜一只钟到整棵树会算会配，你只花了一章。

<div class="achievement">
✅ 下一站：<a href="03-gpio.html">S3 GPIO</a>：七个寄存器逐位拆给你看，E01 那盏灯在这章彻底讲透。
</div>

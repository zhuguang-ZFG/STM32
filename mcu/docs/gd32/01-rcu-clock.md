---
title: G1 RCU 时钟树：200MHz 是怎么算出来的
status: done
difficulty: 3
minutes: 45
---

# G1 RCU 时钟树：200MHz 是怎么算出来的

> 🎯 最危险的移植往往不是完全陌生，而是“看起来一模一样”：PLL 位域熟悉、时钟公式熟悉、输出脚也熟悉，于是你顺手照搬 STM32 的经验。GD32 偏偏在电压回执、Flash 等待与外设时钟源上换了合同。今天的任务不是背另一棵时钟树，而是抓出哪些相似可以复用，哪些相似专门会骗熟手。

## 本章精髓

1. **PLL 寄存器和 STM32 同布局**（PSC/N/P/Q 同位域），但官方参数更激进：VCO 拉到 **400MHz**（STM32 的 N=336），25M 晶振 ÷25 ×400 ÷2 = **200MHz**。
2. **电压档是"三件套"且有回执**：LDOVS → HDEN → HDS，后两者各有就绪标志位 **HDRF/HDSRF**，官方代码真的轮询等待。这和 F405/407 的"写入即生效、无位可等"正好相反。
3. **官方 system 文件不设 Flash 等待周期，而且确实不用设**：UM §2.4.1 实证 WSCNT 是 4 位域 **0~15 档**（比 STM32 的 0~7 宽一倍），且必须先置 FMC_WSEN 才生效；而 GD32F407xx datasheet 开篇明写 168MHz 下 **Flash 零等待**："官方留白"不是偷懒，是这条取指路径本就不需要。两份手册都**不给"频率↔等待"对照表**（全文检索实证），与 ST 在 RM0090 直接给整张表的做法正好相反。

## 先修

- S2 的"六步提频"与"MCO1 对账"思想（方法论完全复用）。
- GD32 命名：`CK_SYS`/`CK_AHB`/`CK_APB1`/`CK_APB2` 对应 STM32 的 SYSCLK/HCLK/PCLK1/PCLK2。

## 先跑起来（10 分钟 quick win）

先遮住下文结论，只看官方 PLL 参数，自己算一遍输入、VCO 与系统时钟；再回答两个迁移判断：STM32 的电压档“写完就走”能否照搬？MCO 的分频编码能否按“分频比减一”填写？算完再往下读。前一道题考公式，后两道题专门抓“太熟所以没查手册”的惯性。

即时判分标准很简单：频率公式可以复用，电压握手不能省，输出分频编码必须查枚举。相似的位域帮你快速定位，不同的状态位与编码才决定代码能不能安全运行。

## 动画：GD32 的时钟树长什么样

![GD32 RCU 时钟树动画](/anim/gd32-rcu-clock.svg)

## 一、命名对照：同名不同姓

时钟树先看图：源、PLL、SYSCLK、AHB/APB 逐级分发；切换顺序铁律在图底。

![GD32 RCU 时钟树：IRC16M/HXTAL→PLL→SYSCLK→AHB→APB 两级](/arch/rcu-tree.png)

| STM32F407 | GD32F4xx | 凭证 |
|---|---|---|
| RCC | **RCU**（基址 0x40023800，AHB1） | gd32f4xx.h:343 |
| SYSCLK / HCLK / PCLK1/2 | **CK_SYS / CK_AHB / CK_APB1/2** | gd32f4xx_rcu.h 注释 |
| HSI 16M / HSE | **IRC16M / HXTAL** | gd32f4xx_rcu.h:812-814 |
| FLASH_ACR.LATENCY | **FMC_WS.WSCNT**（bits[3:0]，0~15 档） | gd32f4xx_fmc.h:150-165 |
| PWR + VOS（无回执） | **PMU + LDOVS/HDEN/HDS**（有 HDRF/HDSRF 回执） | gd32f4xx_pmu.h:59-73 |
| MCO1（PA8，/1~/5，编码 0/4/5/6/7） | **CK_OUT0**（PA8，/1~/5，编码同款） | gd32f4xx_rcu.h:886-901；HAL stm32f4xx_hal_rcc.h:314-318 |
| PLLRDY / SWS | **PLLSTB / SCSS** | gd32f4xx_rcu.h:88,102-103 |

## 二、PLL：同布局，更激进

`RCU_PLL` 偏移 0x04、`RCU_CFG0` 偏移 0x08（gd32f4xx_rcu.h:44-46），与 STM32 的 PLLCFGR/CFGR 排布一致，位域也一样：

```
RCU_PLL = PSC[5:0] | N[14:6] | P[17:16]=(P/2)-1 | SRC[22] | Q[27:24]
```

官方 200M 档写入的参数（system_gd32f4xx.c:946-948）：

```c
RCU_PLL = (25U | (400U << 6U) | (((2U >> 1U) - 1U) << 16U) |
           (RCU_PLLSRC_HXTAL) | (9U << 24U));
```

即 **PSC=25，N=400，P=2，SRC=HXTAL，Q=9**：25MHz ÷ 25 = 1MHz 进 VCO，× 400 = **400MHz**，÷ P2 = **200MHz**。对比 STM32F407 的 8÷8×336÷2=168：公式一模一样，N 的上限更敢用（400 > 336）。

Q=9 给出 400/9 ≈ **44.4MHz**。这里有个值得停一下的细节：**USB 要的是 48MHz，44.4 不是 48**。UM §4.2.2 已核验：USBFS / USBHS / TRNG / SDIO 四个外设统一吃一路叫 **CK48M** 的时钟，而 CK48M 由 **PLLQ / PLLSAIP / IRC48M 三选一**（`RCU_ADDCTL` 的 `PLL48MSEL` + `CK48MSEL` 两位）。所以官方 200MHz 档下 PLLQ 根本凑不出 48MHz，USB 必须改走另外两源。GD32 多给的那颗 **IRC48M（片内 48MHz RC）** 正是为这种场合准备的。

对照着看 ST 的选择就更有意思：STM32F407 **没有** 48MHz 片内 RC，CK48M 只能由 PLLQ 出，所以 ST 把 N 定在 336，336/7 刚好 48.000MHz，提频公式是被 USB 反向约束过的。GD32 敢把 N 推到 400（VCO 400MHz 整），代价是 PLLQ 凑不出整 48，补偿是多给一颗 IRC48M。**同一条公式，两种取舍。**

<ClockCalc />

## 三、电压档三件套：这次真的"等就绪"

GD32 把"能不能上 200MHz"拆成三次握手，每一步都有硬件回执（system_gd32f4xx.c:960-984）：

| 步 | 写什么 | 等什么 | 回执位 |
|---|---|---|---|
| 1 | `PMU_CTL.LDOVS`（bits[14:15]） | 无需等待 | — |
| 2 | `PMU_CTL.HDEN`（bit16）高驱动使能 | `PMU_CS.HDRF`（bit16） | 官方代码真轮询 |
| 3 | `PMU_CTL.HDS`（bit17）切入高驱动 | `PMU_CS.HDSRF`（bit17） | 官方代码真轮询 |

前提：`RCU_APB1EN.PMUEN`（bit28）先给 PMU 时钟，GD32 的 PMU 挂 **APB1**（gd32f4xx_rcu.h:261）。

和 S2 的结论对照着记：**F405/407 的 VOS 没有就绪位，写完就当生效；GD32F4xx 有 HDRF/HDSRF，官方流程必须等**。另外官方文件在提频前还塞了一个 `_soft_delay_()` 软延时，注释明说"防止 Vcore 波动影响，强烈建议保留"（system_gd32f4xx.c:226-231）。电压档切换不是免费的。

## 四、Flash 等待：官方不管，你来管

`system_gd32f4xx.c` 全文件**没有任何 FMC 等待周期设置**；对官方库**全量 Examples（3295 个文件，浅克隆逐目录检索）**搜 `fmc_wscnt_set` / `FMC_WS`，**零命中**。官方示例从不设 Flash 等待。而 FMC 的等待档位实际有 **0~15 共 16 档**，WSCNT 是 4 位域（`FMC_WC_WSCNT = BITS(0,3)`，gd32f4xx_fmc.h:65），头文件给出 WS_WSCNT_0 ~ WS_WSCNT_15 全部宏（:149-165），比 STM32F407 的 0~7（3 位）宽一倍。另外 GD32 还有一枚 STM32 没有的 **FMC_WSEN@0xFC** 等待使能寄存器（`FMC_WSEN_WSEN` bit0，:117-118）。两件套都要自己管。

> ✅ **这个坑已经填了**：官方示例不设等待却跑高频，答案在 datasheet 第一页：GD32F407xx 的 Cortex-M4 "operating at 168 MHz frequency with **Flash accesses zero wait states**"（GD32F407xx Datasheet Rev2.7 §1）。GD32 的 Flash 取指路径按零等待设计，所以官方 system 文件不写 FMC_WS 也能跑满 168MHz。那 WSCNT 存在的意义是什么？UM §2.4.1 的一句话给了线索（"The WSCNT valid when **WSEN** bit in FMC_WSEN is set"）：**等待周期默认整条路关着**，要用得先开 FMC_WSEN@0xFC，这是给特殊电压/温度条件或更高主频档留的余量，不是常规必配项。
>
> ⚠️ 一个诚实的边界：我们手上的 datasheet 是 **F407xx（168MHz 档）**。官方 system 文件默认的 **200MHz 档属于 F450/F470**，那两颗的零等待上限要各自 datasheet 确认，本站**不做外推**。

> ⚠️ 本工程策略：`FMC_WS_VALUE` 宏默认取**保守超配值**（多配等待周期只会稍慢，欠配会取指跑飞）。位域与使能链已全部核验（WSCNT 4 位 0~15 + WSEN 使能，UM §2.4.1 / §2.4.10）；但手册**确实不提供**"频率↔等待"对照表，所以"这颗板子这个频率该配几拍"没有纸面答案，只能上板实测。在没有对照表的情况下，保守超配是唯一安全的默认值。

## 五、CK_OUT0 对账：MCO1 的同岗同事

- 引脚 **PA8，AF0**（官方 CKOUT 示例 gpio_af_set(GPIOA, GPIO_AF_0, GPIO_PIN_8)，example_ckout_main.c:135），和 STM32 MCO1 同脚同 AF。
- 源可选 IRC16M/LXTAL/HXTAL/**PLLP**（gd32f4xx_rcu.h:886-889），分频 **/1 /2 /3 /4 /5**（:897-901），**与 STM32 MCO1 完全同款**：两边都不是 2 的幂序列，编码也一样（0xx=不分频、100=/2、101=/3、110=/4、111=/5；HAL `RCC_MCODIV_1..5`=0/4/5/6/7，stm32f4xx_hal_rcc.h:314-318）。"看名字以为是 STM32 的坑、其实两边一样"本身就是对照阅读的价值。
- 编码雷区：/4 的编码是 **6**，不是 3：写成 3 会掉进"不分频"区。（S2 工程曾真踩此坑，已修。）
- 选 PLLP + /4 → **理论 50MHz** 上 PA8，示波器一量就知时钟树对不对（**待上板实测**）。

## 六、代码分析：`code/gd32/01-rcu-clock/main.c`

工程与 S2 的 `01-rcc-clock` 同构，差异点全部点名：

- `hxtal_enable()`：HXTALEN + 轮询 HXTALSTB，**超时回退 IRC16M**（官方 demo 是 `while(1)` 死等，system_gd32f4xx.c:942-945；教学工程不照抄这个坏习惯）。
- `pmu_highdrive_enter()`：PMUEN → LDOVS → HDEN 等 HDRF → HDS 等 HDSRF，带超时。
- `fmc_ws_set()`：写 FMC_WS.WSCNT。
- `pll_start()`：按官方参数写 RCU_PLL，PLLSTB 带超时。
- `clock_init()`：总线分频 AHB/1、APB2/2、APB1/4（与官方 200M 档一致），SCS=PLLP 后等 SCSS=PLLP。
- `clock_tree_readback()`：从寄存器反推真实时钟树，**源按 SCSS 如实解码**、PLL 频率按 RCU_PLL 参数重算，存进 `g_clock_tree[]`；故障回退路径也报真账（不传"调用方以为的值"）。
- `ckout0_init()`：PA8 配 AF0，CK_OUT0 = PLLP/4。

## 七、上游对照：官方 `system_gd32f4xx.c` 逐条对照（@10d02f4）

| 官方（行号） | 本工程 | 结论 |
|---|---|---|
| HXTALSTB 超时后 `while(1)`（:942-945） | 超时回退 IRC16M + `g_clock_status=1` | 工程更稳；官方 demo 简化了错误路径 |
| PMUEN→LDOVS→HDEN/HDS 等回执（:960-984） | 同序，加超时 | 一致 |
| 不设 FMC_WS（全文检索为空） | 显式设置 + 保守超配 | 工程补上了官方留白 |
| AHB/1、APB2/2、APB1/4（:962-966） | 同 | 一致 |
| PLL 参数 PSC25/N400/P2/Q9（:946-948） | 同 | 一致 |
| SCS=PLLP 后等 SCSS（:993-999） | 同 | 一致 |
| `while(0 != (RCU_CFG0 & RCU_SCSS_IRC16M))`（:208-210） | —— | **官方小瑕疵**：`RCU_SCSS_IRC16M = CFG0_SCSS(0) = 0`（gd32f4xx_rcu.h:817），这个"等回执"恒假、一次都不等。对照 S2 里 HAL 切钟后老老实实轮询 SWS（hal_rcc.c:681）——**官方库也会有空转，读源码时要带脑子**。本工程的回读改为按 SCSS 如实解码，故障路径也不报假账。 |

## 附录：工程完整源码

<<< ../../code/gd32/01-rcu-clock/main.c

## 记忆锚点

::: tip 一句话记住
**先电压三件套（LDOVS→HDEN→HDS 带回执）、再 FMC 等待、后切钟；写完 SCS 看 SCSS；CK_OUT0 一量，自欺现形。**
:::

**延伸**：GD32 RCU 时钟树动画见 [G1 动画](/anim/gd32-rcu-clock.svg)；STM32 RCC 对照见 [S2](../stm32/02-rcc-clock.md)；Flash 等待周期在 [B5](../build/05-map-size.md) 有体积影响。

## 实物实验

- CK_OUT0 量频：构建烧录后量 PA8，应为 ≈50MHz（200/4）；切 IRC16M 档应为 4MHz。
- HSE 对账：量 HXTAL 实际频率（晶振标称 25M 常有 ±20ppm 偏差），回填到 `HXTAL_VALUE_HZ`。
- 翻车实验（选做）：把 FMC_WS 改小 2 档跑 200MHz，观察取指异常，再用调试器读 FMC_WS 复位值。

## 常见坑

1. **PMU 时钟没开就写 PMU_CTL**：`RCU_APB1EN.PMUEN`（bit28）是第一步，否则写进去的影子都没有。
2. **照抄官方 demo 的 `while(1)`**：晶振不来就死机；教学工程的超时回退才配叫"代码"。
3. **以为官方帮你设了 Flash 等待**：`system_gd32f4xx.c` 不设 FMC_WS，欠配等待周期上 200M 必跑飞。

## 短自测

1. GD32F450 官方默认档从 25MHz HXTAL 算到 200MHz，写全 PLL 公式。和 STM32F407 的 N=336 有什么差别？
<details><summary>参考答案</summary>公式：25MHz ÷ 25（PSC=24，分频系数=PSC+1=25）× 400（N=399，倍频系数=N+1=400）÷ 2（P=1，分频系数=P+1=2）= **200MHz**。VCO 频率 = 25 ÷ 25 × 400 = 400MHz。STM32F407 的 VCO 封顶 336MHz（N=335），SYSCLK = VCO ÷ 2 = 168MHz。GD32 把 VCO 拉到 400MHz，同样 ÷2 就是 200MHz。PLL 寄存器布局完全相同，只是参数更激进。</details>

2. HDEN 和 HDS 各控制什么？为什么两个都要等标志位？
<details><summary>参考答案</summary>**HDEN**（High Density Mode Enable）使能高密度模式，拉高 LDO 输出，让芯片能在 200MHz 下稳定运行。**HDS**（High Density Step）进一步微调 LDO 档位到最高性能档。两者各有就绪标志：**HDRF**（HD Enable Ready Flag）和 **HDSRF**（HD Step Ready Flag）。必须轮询等待是因为 LDO 电压爬升需要时间（微秒级），如果不等就绪就提频，内核可能因供电不足跑飞。官方 `system_gd32f4xx.c` 里两步都有 `while(!HDRF)` / `while(!HDSRF)` 的等待循环。</details>

3. CK_OUT0 输出在哪个引脚？/4 分频的编码值是多少？误写成"分频比 − 1 = 3"会落入哪个编码区？
<details><summary>参考答案</summary>CK_OUT0 输出在 **PA8**（AF0 复用功能）。/4 分频的编码值是 **6**：官方宏依次使用 0、4、5、6、7 表示 /1 到 /5。误写 3 会落入 `0xx` 的不分频区，输出源时钟而不是 /4。这里不能套“分频系数减一”，必须按官方枚举写值；本章代码使用的 `RCU_CKOUT0_DIV4` 也正是 `6UL << 24`。</details>

## 事实来源

| 结论 | 出处 |
|---|---|
| RCU 基址/外设库命名 | gd32f4xx.h:343（@10d02f4） |
| CTL/PLL/CFG0 偏移 0x00/0x04/0x08，AHB1EN 0x30，APB1EN 0x40 | gd32f4xx_rcu.h:44-56 |
| HXTALEN/HXTALSTB bit16/17，PLLEN/PLLSTB bit24/25 | gd32f4xx_rcu.h:83-88 |
| SCS/SCSS/AHBPSC/APB1PSC/APB2PSC/CKOUT0 位域 | gd32f4xx_rcu.h:102-112 |
| 官方 200M 档 PLL 参数与提频序列 | system_gd32f4xx.c:936-1003 |
| LDOVS/HDEN/HDS 与 HDRF/HDSRF | gd32f4xx_pmu.h:59-73 |
| PMUEN bit28 | gd32f4xx_rcu.h:261 |
| FMC_WS.WSCNT 0~15 档 + FMC_WSEN 使能 | gd32f4xx_fmc.h:65,117-118,149-165（V3.3.3 已核验） |
| WSCNT 必须 WSEN 置位才生效 | **UM Rev3.0 §2.4.1 / §2.4.10 已核验**（p69 / p76） |
| 168MHz 下 Flash 零等待 | **GD32F407xx Datasheet Rev2.7 §1 已核验**（F450/F470 的 200/240MHz 档未外推） |
| UM 与 datasheet 均无"频率↔等待"对照表 | 两份手册全文检索零命中（已核验） |
| CK48M 三源 PLLQ/PLLSAIP/IRC48M，由 RCU_ADDCTL 的 PLL48MSEL+CK48MSEL 选 | **UM Rev3.0 §4.2.2 已核验**（p94） |
| PA8 AF0 配 CK_OUT0 | example_ckout_main.c:135（@10d02f4）+ **datasheet §2.6.6 Table 2-9 AF0 列已核验** |

## 你做到了

- 你算出了 GD32 的 200MHz，也掌握了“同名不同姓”的对照读法。拿到任何一颗 Cortex-M4，都能顺着时钟树把它提上去。
- 你知道电压档要等回执、Flash 等待要自己管：这两条是官方文档不会替你记住的坑。

回到开场那次“看起来一样”的移植：你现在会先复用结构，再逐项核对合同。公式相同就大胆算，状态位不同就老实等，编码表长得眼熟也要重新查。真正可迁移的不是寄存器写法，而是这套对照取证的方法。

<div class="achievement"> ✅ G1 收官。下一站：<a href="./02-gpio-af.html">G2 GPIO 与 AF 复用对照</a>：七大寄存器“同名不同姓”，逐个点名。 </div>

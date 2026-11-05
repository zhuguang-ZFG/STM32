---
title: S14 低功耗：让电池活过一年
status: done
difficulty: 2
minutes: 50
---

# S14 低功耗：三种睡眠的唤醒与代价

> 🎯 电池产品的灵魂拷问：99% 的时间你的设备在睡觉。睡眠有多深、醒得多快、醒来还记得什么，决定了电池活一个月还是一年。

## 本章精髓

1. 三档睡眠的取舍：**Sleep**（只停 CPU，外设全醒，µs 级唤醒）→ **Stop**（停 1.2V 域时钟，SRAM/寄存器保留，RTC/EXTI 唤醒，µA~几十µA）→ **Standby**（几乎全断电，只留备份域，nA~µA，但 SRAM 全丢、复位式唤醒）。
2. 唤醒源是设计出来的：EXTI/RTC 闹钟/WKUP 引脚/IWDG。"谁能叫醒我"必须在入睡前配好，漏配=睡死。
3. 省电不止睡：降频、关外设时钟、GPIO 模拟态、关调试接口（DBGMCU 在 Stop 下也吃电）。系统级抠电。

- **能理解**：为什么 Stop 醒来后系统跑在 HSI 16MHz（PLL 停了得重配）；为什么 Standby 唤醒是"复位"而不是"继续"。
- **能用**：进 Stop + RTC 闹钟周期唤醒，万用表量到电流从 mA 掉到 µA 的跳水。

## 先修

- [S2 时钟](02-rcc-clock.md)、[S4 EXTI](04-nvic-exti.md)、[S5 SysTick](05-systick.md)。

## 先跑起来（10 分钟 quick win）

**没有板子也能把本章的账全跑完**。进 `code/stm32/14-pwr`：

```bash
sh probe.sh          # 三步：宿主跑固件自己的函数 → 位号/地址与 CMSIS 逐条对账 → 交叉链 -O2 反汇编三档睡眠
```

第 1 步把 `PWR_CR`/`PWR_CSR`/`RCC_*`/`SCB_SCR`/`DBGMCU_CR`/`SysTick_LOAD`/`BKPSRAM_BASE` 全部改指到一组假寄存器再 `#include "main.c"`，所以断言跑的是固件本体：三档各自写出的那两个位（`Sleep CR=0x4200 SCR=0x10`、`Stop CR=0x4201 SCR=0x14`、`Standby CR=0x4202 SCR=0x14`）、醒来那笔时钟账（1 ms 变 10.5 ms、115200 变 **10973**）、看门狗八个分频码、备份域四笔解锁、唤醒源矩阵、复位原因解码。第 2 步把本章列出的**每一条位号**和 **10 个寄存器地址**拿去和 ST 官方 CMSIS 头文件逐条 diff（地址那一遍是现场从头文件的 `base + 结构体成员 Offset` 注释拼出来的，脚本里一个地址都没写死）。第 3 步把 `main.c` 编成 Cortex-M4 的 `-O2` 目标文件，三档睡眠在指令流里就是「改 CR + 改 SCR + `dsb sy` + `wfi`」，而 `wfi` 之后剩多少条指令，恰好是三档的本质差别（实测 1 / 6 / 7 条，见第八节）。

有板子再加一步：主循环跑 5 秒→进 Stop→RTC 2 秒后唤醒→串口打印"我醒了"循环，万用表串在供电上，看电流从 mA 掉到 µA 的跳水瞬间。

睡前先押个失忆：Standby 睡上一整晚再醒来，主 SRAM 和备份 SRAM，谁还记得睡前的事？两个都忘、都记得，还是只留一个在守夜？押完往下读，看备份域凭什么能撑过长夜。

## 动画：低功耗三档对比

Sleep 只停 CPU、Stop 停 1.2V 域时钟保留 SRAM、Standby 几乎全断电。三档"停什么/留什么/谁唤醒/醒来到哪"逐档对照，深睡与快醒的取舍一目了然。

![低功耗三档对比：Sleep/Stop/Standby](/anim/stm32-pwr-three-modes.svg)

## 板卡事实

- PWR 控制器基址 `PWR_BASE = APB1 + 0x7000 = 0x40007000`（CMSIS 已核对）；时钟在 RCC_APB1ENR bit28 = `RCC_APB1ENR_PWREN_Msk`。
- PWR_CR 关键位：`LPDS`（bit0，Stop 下调压器低功耗）、`PDDS`（bit1，=1 进 Standby）、`CWUF`（bit2，清唤醒标志）、`CSBF`（bit3，清 Standby 标志）、`DBP`（bit8，解除备份域写保护）、`FPDS`（bit9，Stop 下 Flash 掉电），CMSIS 逐位核对。
- PWR_CSR 关键位：`WUF`（bit0，唤醒标志）、`SBF`（bit1，Standby 标志）、`BRR`（bit3，备份调压器**就绪**）、`EWUP`（bit8，使能 WKUP 引脚 PA0）、`BRE`（bit9，备份调压器**使能**）。`BRR`/`BRE` 这两位本章第五节要用，探针实测它们各自管什么。
- 内核那一侧只有一个位定档：`SCB->SCR`（`0xE000ED10`）的 `SLEEPDEEP`（bit2）；`SLEEPONEXIT`（bit1）与 `SEVONPEND`（bit4）是两个会被睡眠顺带动到的邻居位，实测它们不被定档逻辑碰。
- `RCC_CSR`（`0x40023874`）高位的七个复位标志：`RMVF`（bit24，写 1 清全部）、`BORRSTF` 25、`PINRSTF` 26、`PORRSTF` 27、`SFTRSTF` 28、`IWDGRSTF` 29、`WWDGRSTF` 30、`LPWRRSTF` 31。
- `DBGMCU_CR`（`0xE0042004`）低三位 `DBG_SLEEP`/`DBG_STOP`/`DBG_STANDBY`（bit0/1/2），睡前一次 `bic #7` 清掉。
- 备份 SRAM **4 KB** 在 `BKPSRAM_BASE = 0x40024000`（CMSIS 已核对），时钟在 RCC_AHB1ENR bit18 = `RCC_AHB1ENR_BKPSRAMEN_Msk`（0x40000）；写之前必须 `PWR_CR.DBP=1` 解除备份域写保护。4096 字节 = **1024 个 32 位字**，这是"睡前遗言"的硬上限。
- Stop 唤醒源在线路层的落点：`WKUP` = EXTI 线 **0**（PA0，但由 `PWR_CSR.EWUP` 单独管，不在 EXTI_IMR 里）、`PVD` = 线 16、`RTC 闹钟` = 线 **17**、`RTC 唤醒` = 线 18。
- RTC 基址 `RTC_BASE = APB1 + 0x2800 = 0x40002800`；时钟使能在 RCC_BDCR.RTCEN（bit15），时钟源选 LSE/LSI（RCC_BDCR.RTCSEL）。
- IWDG 预分频寄存器 `PR` 是 **3 位（8 个码）但只有 7 档分频**：`/4 /8 /16 /32 /64 /128 /256 /256`。`PR=6` 与 `PR=7` 是同一个 256，不存在 /512。LSI 按 32 kHz 算，`RLR=4095` 时超时从 511 ms（PR=0）到 32760 ms（PR=6/7）。
- 电流数值以 F407 datasheet §"Power consumption"为准，本章给量级（mA → µA → µA/nA）而非具体数，实测见 [E06](../lab/e06-lowpower-current.md)。

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 三档对比 | 四列对照表 + 唤醒延迟实测数据 | 配置 |
| Sleep 与 WFI/WFE | `__WFI()` 一条指令的事；唤醒后时钟恢复检查 | 代码分析 |
| Stop 全流程 | 入睡前配置清单；唤醒后重配 PLL（HSI 默认接管） | 代码分析 |
| RTC 闹钟 | RTC 初始化与闹钟中断；LSI/LSE 精度对续航的影响 | 配置 |
| Standby 与备份域 | 备份寄存器传"睡前遗言"；WKUP 引脚 | 代码分析 |
| 抠电清单 | GPIO/调试接口/外设时钟/调压器档位逐项抠 | 配置 |
| SPL 对照 | PWR_EnterSTOPMode 的参数含义 | 库解析 |
| 无板取证 | `code/stm32/14-pwr/probe.sh`：固件本体跑断言 + CMSIS 逐位逐址对账 + `-O2` 反汇编三档睡眠 | 代码分析 |

## 一、三档对比：停什么、留什么、谁唤醒、醒来到哪

供电域矩阵先看图：深底是断电的域——Run 全活，Stop 停 1.2V 域时钟但 SRAM/RTC 还在，Standby 只剩备份域守夜。

![三档睡眠供电域矩阵：深底为断电域，Standby 只留 RTC 与备份 SRAM](/arch/pwr-domains.png)

低功耗不是"省电模式"一个词，是一张取舍表。F407 提供三档，越深越省电，但醒来代价越大：

| 维度 | Sleep | Stop | Standby |
|---|---|---|---|
| **停什么** | CPU 时钟 | 1.2V 域时钟（CPU+大部分外设） | 调压器（1.2V 域断电） |
| **留什么** | SRAM、寄存器、所有外设时钟 | SRAM、寄存器、RTC、备份域 | **只有备份域**（备份寄存器+备份 SRAM） |
| **谁唤醒** | 任何使能的中断 | EXTI（上升/下降沿）、RTC 闹钟、部分外设 | WKUP 引脚（PA0）、RTC 闹钟、IWDG 复位、NRST |
| **醒来到哪** | WFI 的下一条指令 | WFI 的下一条指令（但 HSI 接管时钟） | **复位入口**（像重新上电） |
| **唤醒延迟** | µs 级 | µs 级（时钟要重启） | ms 级（调压器重启+复位） |
| **电流量级** | 接近运行（mA） | µA ~ 几十 µA | µA ~ nA |
| **核心寄存器** | SCB->SCR.SLEEPDEEP=0 | SCR.SLEEPDEEP=1 + PWR_CR.PDDS=0 | SCR.SLEEPDEEP=1 + PWR_CR.PDDS=1 |

读这张表的方法是"看代价"：Sleep 最浅（什么都没忘，但也没省多少）；Standby 最深（SRAM 全丢，醒来像重生，但电流最低）。**选哪档取决于"醒来还需要记得什么"**：要无缝继续 → Stop；可以接受重置 → Standby。

**对照阅读**：ESP32-S3 的低功耗策略在 [P11](../esp32/11-lowpower.md)，架构不同但取舍相似：STM32 靠硬件模式切换，ESP32 靠 light/deep sleep + ULP 协处理器守夜。两条线对照看，低功耗设计的"停什么/留什么/谁唤醒"三问是通用的。

![低功耗三档：Sleep 只停 CPU，Stop 停时钟保 SRAM，Standby 全停且唤醒相当于复位](/figures/stm32-14-pwr.svg)

## 二、Sleep 与 WFI/WFE：一条指令的事

Sleep 是最轻的，只停 CPU 时钟，外设全活：

```c
#include "stm32f407.h"   /* CMSIS：SCB + __WFI/__WFE 内建 */

static void enter_sleep(void)
{
    SCB->SCR &= ~SCB_SCR_SLEEPDEEP_Msk;     /* SLEEPDEEP=0 → Sleep（不是 Stop） */
    __WFI();                                /* Wait For Interrupt：CPU 停在这里 */
    /* 任何使能的中断触发后，CPU 在这里醒来，执行 ISR 后回到 WFI 下一条 */
}
```

`__WFI()` 是一条 ARM 指令（CMSIS-Core 内建），CPU 停在这里直到中断到来。Sleep 的用途是"等事件"，主循环没事干时进 Sleep，比 `while(1){}` 死循环省 CPU 那一份动态功耗。唤醒后**时钟没变**（PLL 还在跑），不用重配。

WFE（Wait For Event）是变体：靠事件而非中断唤醒，可以用 `SEV` 指令跨核发事件（双核场景）。单核裸机绝大多数用 WFI。

## 三、Stop 全流程：入睡前清单 + 醒来重配 PLL

Stop 比 Sleep 深一档：1.2V 域时钟全停，但 SRAM 与寄存器保留。代价是醒来后**HSI 16MHz 默认接管**（PLL 在 Stop 期间也停了），系统时钟从 168MHz 掉到 16MHz。倍率是 `168/16 = 10.5`，不是"十倍左右"，`probe.sh` 第 1 步实测：1 ms 的装载值运行档是 `167999`、醒来档是 `15999`；`167999` 不改就带着它回 16MHz，真实周期变成 **10500 µs**，也就是"以为 1 ms，量出来 10.5 ms"。

```c
static void enter_stop(void)
{
    /* 入睡前清单 */
    RCC->AHB1ENR |= RCC_AHB1ENR_GPIOAEN_Msk;   /* 确保 GPIO 时钟开着才能改模式 */
    /* 1. 抠电：未用 GPIO 设模拟输入（见第六节清单） */
    /* 2. 关掉不需要的外设时钟（ADC、SPI 等若不用） */
    /* 3. 可选：Flash 在 Stop 下掉电（FPDS=1），更省一点 */
    PWR->CR |= PWR_CR_FPDS_Msk;

    /* 4. 选 Stop 模式：SLEEPDEEP=1 + PDDS=0 + 调压器低功耗 */
    SCB->SCR |= SCB_SCR_SLEEPDEEP_Msk;        /* SLEEPDEEP=1 → 进深睡 */
    PWR->CR &= ~PWR_CR_PDDS_Msk;              /* PDDS=0 → Stop（不是 Standby） */
    PWR->CR |= PWR_CR_LPDS_Msk;               /* LPDS=1：调压器进低功耗档 */

    __WFI();                                  /* 进 Stop——电流跳水到 µA */

    /* 5. 醒来：HSI 16MHz 接管，必须立刻重配 PLL */
    SystemClock_Config();                      /* 恢复 PLL 168MHz（[S2](02-rcc-clock.md) 的配置函数） */
    /* 醒来后第一件事检查 PWR_CSR.WUF（bit0）：是哪个唤醒源叫醒的 */
    if (PWR->CSR & PWR_CSR_WUF_Msk) {
        PWR->CR |= PWR_CR_CWUF_Msk;            /* 清 WUF：写 CWUF（bit2）清 */
    }
}
```

唤醒源必须在**入睡前**配好：EXTI 配上升沿（[S4](04-nvic-exti.md)）、RTC 闹钟（第四节）。Stop 唤醒是"继续"。WFI 下一条指令，但若忘了重配 PLL，程序会以为还在 168MHz，所有定时器慢 10.5 倍，串口更直接：`BRR=729` 是按 `PCLK2=84MHz` 算出来的 115226.0 baud（误差 +0.023%），醒来 `PCLK2` 掉到 8MHz 后那个 729 变成**实际打出去 10973 baud**。对面那台终端一个字节都收不到。这两笔账都不是崩溃，是"看起来在跑、数全错"，典型的"醒来变痴呆"。

## 四、RTC 闹钟：周期唤醒的精准节拍

RTC 是 Stop/Standby 下唯一还在走的外设（靠 LSE/LSI 独立时钟），所以是周期唤醒的首选。配置链路（RTC 在备份域，写前要 DBP）：

```c
static void rtc_alarm_init_for_wakeup(uint32_t seconds)
{
    RCC->APB1ENR |= RCC_APB1ENR_PWREN_Msk;
    PWR->CR |= PWR_CR_DBP_Msk;                /* 解除备份域写保护（动 RTC 必备） */
    /* 时钟源选 LSE（外部 32.768kHz 晶振，精度高）或 LSI（内部 RC，省一个晶振但精度差） */
    RCC->BDCR |= RCC_BDCR_RTCEN_Msk;          /* 使能 RTC（RCC_BDCR bit15） */
    /* 选时钟源、配置 RTC 预分频与闹钟寄存器——细节以 RM0090 RTC 章为准 */
    /* 闹钟中断经 RTC_Alarm_IRQn → EXTI Line 17 唤醒（[S4](04-nvic-exti.md) 的 EXTI 路由） */
    /* 设闹钟 = 当前时间 + seconds，周期唤醒由"闹钟中断里重设下一次"实现 */
}
```

LSI vs LSE 的取舍直接关系续航：**LSE**（外部 32.768kHz）精度高（±20ppm）、功耗极低，是 RTC 标配；**LSI**（内部 RC，约 32kHz）省一个外部晶振但精度差（±5%）、随温度漂，长期定时（闹钟日历）必须 LSE，短时唤醒（"每 2 秒醒一次"）LSI 够用。RTC 闹钟唤醒经 EXTI Line 17（[S4](04-nvic-exti.md)），所以"RTC 唤醒 Stop"在硬件层面就是"EXTI 17 上升沿"。

## 五、Standby 与备份域：只留遗言的深度睡眠

Standby 是最深的，调压器关掉，1.2V 域断电，SRAM 全丢。醒来**不是继续**，是**复位**（PC 从 0 起跑，像重新上电）。唯一活下来的是备份域：备份寄存器（20 个 32 位字，RTC 寄存器区）+ 备份 SRAM（4KB）。

```c
static void enter_standby_with_message(const uint32_t *msg, uint32_t n)
{
    /* 1. 把"睡前遗言"写进备份 SRAM（Standby 后还在）——四笔解锁，一笔都不能少 */
    RCC->APB1ENR |= RCC_APB1ENR_PWREN_Msk;          /* bit28：不开 PWR 时钟，后面全白写 */
    PWR->CR  |= PWR_CR_DBP_Msk;                     /* bit8 ：解除备份域写保护          */
    PWR->CSR |= PWR_CSR_BRE_Msk;                    /* bit9 ：开备份调压器（Standby 下给备份域供电）*/
    RCC->AHB1ENR |= RCC_AHB1ENR_BKPSRAMEN_Msk;      /* bit18：开备份 SRAM 时钟          */
    uint32_t *bkp = (uint32_t *)BKPSRAM_BASE;       /* 0x40024000，4KB = 1024 个字 */
    for (uint32_t i = 0; i < n && i < 1024; i++) bkp[i] = msg[i];

    /* 2. 清旧标志、配唤醒源 */
    PWR->CR |= PWR_CR_CWUF_Msk | PWR_CR_CSBF_Msk;  /* 清 WUF/SBF */
    PWR->CSR |= PWR_CSR_EWUP_Msk;                  /* 使能 WKUP 引脚（PA0） */

    /* 3. 进 Standby：SLEEPDEEP=1 + PDDS=1 */
    SCB->SCR |= SCB_SCR_SLEEPDEEP_Msk;
    PWR->CR |= PWR_CR_PDDS_Msk;                    /* PDDS=1 → Standby */
    __WFI();                                       /* 进 Standby——不会返回 */

    /* 醒来 = 复位：从这里开始重来，靠 SBF 判断"我是不是刚从 Standby 醒来" */
}
```

**这四位里最容易被漏的是 `BRE`（bit9，备份调压器使能）**：`DBP` 管的是"写保护"，`BRE` 管的是"给备份域供电"，两件事。Standby 期间主调压器关掉，备份域靠这个独立的备份调压器活着。没开它，写进 `BKPSRAM` 的东西醒来一定不在。`probe.sh` 的写法是把这三关做成一个函数，逐关返回码可查（实测：`DBP=0` 就写 → **−1**，`DBP` 有但 `BRE` 没开 → **−2**，`n > 1024` → **−3**，三关全过 → **0**，且前两关失败时 `f_bkpsram[0]` 断言仍为 0——**写进去的确实是空气**）。对应的就绪位是 `PWR_CSR.BRR`（bit3）：`BRE` 是使能，`BRR` 是回执，探针里两遍调用实测出"第一遍回执 1（没就绪）、置上 `BRR` 之后第二遍回执 0（就绪）"。**动备份域之前等的是 BRR，不是 BRE**。

顺带一提，`bkp_store()` 那种"越界就整笔拒掉（−3）"而不是"写到 1024 个字为止"的取舍：遗言写一半比写不下更糟，因为醒来那份状态看起来是完整的。

复位后怎么知道"是上电"还是"刚从 Standby 醒来"？查 PWR_CSR.SBF（bit1）：

```c
/* 在 reset handler 或 main 早期 */
if (PWR->CSR & PWR_CSR_SBF_Msk) {
    /* 是从 Standby 醒来，备份 SRAM 里的遗言还在 */
    PWR->CR |= PWR_CR_CSBF_Msk;     /* 清 SBF，下次上电就不会误判 */
    /* 读 BKPSRAM 取遗言 */
} else {
    /* 真上电，备份 SRAM 是 0 或上次值——按上电处理 */
}
```

"醒来是复位"是 Standby 与 Stop 的本质区别：Stop 醒来继续跑（只需重配时钟），Standby 醒来重生（要从备份域捡回状态）。设计取舍很直接：要无缝继续 → Stop；可以接受重置且要极致省电 → Standby。

但 `SBF` 只回答"是不是从 Standby 醒的"，不回答"这一笔是谁给的复位"。真上电、看门狗咬、软复位、欠压，在代码看来都是"我从 0 起跑"，分辨它们靠 `RCC_CSR` 高位那七个标志。`probe.sh` 把解码函数喂了五组实测标志位（第 7 节，断言全绿）：

| 现场 | `RCC_CSR` | `PWR_CSR` | 解码出的位图 | 读法 |
|---|---|---|---|---|
| 刚上电 | `0x0C000000` | `0x00000000` | `0x0C` | POR + PIN（`NRST` 也被拉过） |
| Standby 醒来 | `0x08000000` | `0x00000002` | `0x09` | `SBF` + `PORRSTF`——Standby 的"醒"走的是上电复位那条序列，两个标志一起置起（口径以 RM0090 复位章为准） |
| 看门狗咬的 | `0x20000000` | `0x00000000` | `0x20` | `IWDGRSTF`，没有 SBF |
| 软复位 | `0x10000000` | `0x00000000` | `0x10` | `SFTRSTF`（NVIC 系统复位请求） |
| 欠压 + BOR | `0x82000000` | `0x00000000` | `0x82` | `BORRSTF` + `LPWRRSTF` |

**读完必须写 `RCC_CSR.RMVF`（bit24）清标志**：否则下一次开机照抄这一次的结论，把"上次是狗咬的"当成"这次也是"。探针里的动作断言只断言"固件发出了那个写"（假寄存器不会自己变，硬说硬件清了就是自欺）。

## 六、抠电清单：睡前的系统级准备

光进低功耗模式不够，"漏电"的元凶常常是没伺候好的外设。入睡前逐项检查：

1. **未用 GPIO 设模拟输入**：悬空的数字输入脚在漏电流上"喝电"，配成模拟输入（MODER=0b11）或确定上下拉，把漏电流通道关掉；
2. **关掉不需要的外设时钟**：ADC、SPI、USART 若不用，RCC 位清掉，外设静态功耗归零；
3. **关调试接口**：DBGMCU->CR 的 `DBG_SLEEP` / `DBG_STOP` / `DBG_STANDBY`（bit0/1/2）若置着，Stop/Standby 下调试器还吃电，实测功耗时**必须拔掉仿真器**并清这三位，否则电流虚高一个数量级。固件里就一句 `DBGMCU->CR &= ~(7U << 0)`，`-O2` 编出来是一条 `bic.w r3, r3, #7`（`probe.sh` 第 3 步实测，见第八节）；
4. **调压器档位**：Stop 下用 LPDS=1（低功耗档）；F4 的 VOS（电压调节输出）在运行时也能降档（PWR_CR.VOS，bit14），降一档省一档电，代价是最高频率受限（[S2](02-rcc-clock.md) 里 VOS='0' 时 fHCLK 上限只有 144MHz）；
5. **Flash 掉电**：FPDS=1 让 Flash 在 Stop 下断电，省一点，代价是唤醒后第一次取指稍慢；
6. **IWDG 还在跑**：[S5](05-systick.md) 提过 IWDG 靠 LSI 独立跑，Stop 期间也计数，若 Stop 时间超过 IWDG 超时，醒来就不是"唤醒"而是 IWDG 复位。要么睡前喂狗+算好超时，要么进 Stop 前关 IWDG（但关了就没了看门狗保护）。

第 6 项那笔账必须算，因为 `PR` 那个字段有个坑：**3 位宽 = 8 个码，但只有 7 档分频**。`probe.sh` 第 4 节把八个码全跑了一遍（LSI 按 32 kHz、`RLR=4095` 上限，本机实跑）：

| `PR` | 0 | 1 | 2 | 3 | 4 | 5 | **6** | **7** |
|---|---|---|---|---|---|---|---|---|
| 分频 | /4 | /8 | /16 | /32 | /64 | /128 | /256 | **/256** |
| 超时 ms | 511 | 1023 | 2047 | 4095 | 8190 | 16380 | 32760 | **32760** |
| LSI ±5% | 485~536 | 971~1074 | 1944~2149 | 3890~4299 | 7780~8599 | 15561~17199 | 31122~34398 | 同左 |

按"8 个码就是 /4×2⁷ = /512"去想，会把最长超时算成 **65520 ms**（探针把这一版也当场算了一遍贴在旁边），正好是实际值的两倍，而 LSI 本身 ±5% 的漂移盖不住这个错误。写代码时 `div = 4 << pr` 是错的，要么查表、要么 `pr >= 6 ? 256 : (4 << pr)`（本工程用查表，`probe.sh` 断言 `PR=6 与 PR=7 同一个分频`）。

这张清单的全部项都能在 [E06](../lab/e06-lowpower-current.md) 实测里逐一开/关对比，每关一项量一次电流，量化每一项的省电贡献。

## 七、SPL 对照：`PWR_EnterSTOPMode` 的参数

SPL 把"进 Stop"包成一个函数（stm32f4xx_pwr.c V1.8.0）：

```c
void PWR_EnterSTOPMode(uint32_t PWR_Regulator, uint8_t PWR_STOPEntry)
{
    /* PWR_Regulator: PWR_Regulator_LowPower → LPDS=1；PWR_Regulator_ON → LPDS=0 */
    /* PWR_STOPEntry: PWR_STOPEntry_WFI / PWR_STOPEntry_WFE */
    tmpreg = PWR->CR;
    if (PWR_Regulator == PWR_Regulator_LowPower) tmpreg |= PWR_CR_LPDS;
    else tmpreg &= ~PWR_CR_LPDS;
    PWR->CR = tmpreg;
    SCB->SCR |= SCB_SCR_SLEEPDEEP_Msk;       /* 第三节逐行版 */
    if (PWR_STOPEntry == PWR_STOPEntry_WFI) __WFI();
    else __WFE();
    /* 醒来后 SPL 不替你重配 PLL——这是用户的责任（坑列表第一名） */
}
```

看一眼就明白：SPL 的 `PWR_EnterSTOPMode` 就是第三节的几行寄存器序列，参数 `PWR_Regulator` 选调压器档位、`PWR_STOPEntry` 选 WFI 还是 WFE。**SPL 不替你重配 PLL**：醒来后时钟恢复仍是用户责任（这是为什么"Stop 醒来变痴呆"是 SPL 用户和寄存器用户共同的坑）。`PWR_EnterSTANDBYMode` 同理：设 PDDS + SLEEPDEEP + WFI，不返回。

读库姿势照旧（[S15](15-spl-anatomy.md)）：拿到 `PWR_EnterSTOPMode` 先问"它动了 CR 与 SCR 的哪几位"，逐位与第三节对答案，低功耗的"魔法"全在 PDDS/LPDS/SLEEPDEEP 这三个位上，库没多做什么。

## 八、`probe.sh`：把这一章的账全部搬到宿主机上跑

手法与 [S2](02-rcc-clock.md) 那一章相同：`probe.c` 先把 `PWR_CR`/`PWR_CSR`/`RCC_APB1ENR`/`RCC_AHB1ENR`/`RCC_BDCR`/`RCC_CSR`/`SCB_SCR`/`DBGMCU_CR`/`SysTick_LOAD` 九个宏改指到一组 `static volatile uint32_t` 假寄存器（`BKPSRAM_BASE` 改指一个 1024 字的数组），再 `#define MCU_PROBE_NO_MAIN` + `#include "main.c"`。于是每条断言跑的都是**固件本体**：`pwr_mode_words` / `enter_sleep` / `enter_stop` / `enter_standby` / `backup_domain_unlock` / `bkp_store` / `wake_source_armed` / `iwdg_timeout_ms` / `usart_baud_from_brr` / `reset_cause_decode` / `firmware_main`。

有一条纪律值得单独说：假寄存器**不会自己变**。所以凡是"硬件会清掉标志 / 硬件会就绪"的地方，探针只断言"固件发出了那个动作"（写 `CWUF`、写 `RMVF`），绝不冒充硬件的回执。

本机实跑（x86 gcc 16.1.0 + xPack ARM 15.2.1，`sh probe.sh`，三步全绿退出 0）。九个探针小节，结论都已落在正文对应那节，这里只留一张"哪一节被哪一遍跑过"的对照，不重复议价：

| 探针小节 | 结论在哪 | 探针小节 | 结论在哪 |
|---|---|---|---|
| §1 三档定档 | 第三节 | §6 唤醒源矩阵 | 第四节 |
| §2 位号表（29 条） | 本节第 2 步 | §7 复位原因解码 | 第五节 |
| §3 醒来时钟账 | 第三节 | §8 固件本体 | 本节下段 |
| §4 IWDG 八码 | 第六节 | §9 地址表（10 个） | 本节第 2 步 |
| §5 备份域四笔 | 第五节 | 三档机身指令 | 本节第 3 步 |

只有 §8 那几个数是正文别处没出现的：把 `firmware_main()` 整跑一遍，得到 `CR=0x4205`、`SCR=0x4`、`DBGMCU_CR=0x30`（`0x37 & ~0x07`，其余位保留）、`SysTick_LOAD=0x3E7F`；这一遍发了 `CWUF`、没发 `CSBF`。把现场换成 `SBF=1` 再跑：发了 `CSBF`、没发 `CWUF`。单独调三个 `enter_*`：`SLEEPDEEP` 依次 0/1/1、`PDDS` 依次 0/0/1，并且 **Standby 那条路径不碰 SysTick 装载值**，醒来是复位，那个变量早就不存在了。

### 第 2 步：位号和地址都不是我说的，是头文件说的

`probe.sh` 的第 2 步先从探针输出里挖出那两块表，再回 CMSIS 挖对照组：位号一侧 `grep` 出全部 `#define XXX_Pos`；地址一侧顺着 `PERIPH_BASE → AHB1PERIPH_BASE → RCC_BASE`、`SCS_BASE → SCB_BASE / SysTick_BASE` 把这些宏里的 `+ 0x...UL` **一段段现挖**再相加，成员偏移则从结构体定义的 `Address offset:` 注释里取。`APB1PERIPH_BASE` 那条脚本会先断言它确实等于 `PERIPH_BASE`（没有隐藏偏移），否则 `PWR_BASE` 那条链就白算。两侧 `diff` 必须为空：

```
  位号对账：29 条逐位一致（diff 为空）
  地址对账：10 个全中（diff 为空）
    PWR_CR 0x40007000        ← 左：CMSIS 拼的   右：固件那一遍打印的
    SCB_SCR 0xE000ED10       ← 内核外设，不在 STM32 地址空间里
    SysTick_LOAD 0xE000E014
    DBGMCU_CR 0xE0042004
    BKPSRAM 0x40024000
```

### 第 3 步：三档睡眠在指令流里长什么样

`main.c` 用板上那套参数编一遍（`-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard -std=c11 -Wall -Wextra -Werror -O2 -c`，只编不链），`size` 回 **text 796 / data 4 / bss 4**。三档的机身分别是（完整机身见 `probe.sh` 第 3 步输出）：

```
enter_sleep :  ldr r0,[PWR_CR] → str r0,[PWR_CR]      ← 读出来原样写回去，中间一条修改都没有
               ldr r3,[SCB+0xd10] → bic r3,#4 → str   ← 只清 SLEEPDEEP(bit2)
               dsb sy → wfi → bx lr                   ← wfi 之后：1 条指令 / 2 字节

enter_stop  :  bic r3,#2 → orr r3,#1                  ← PDDS=0、LPDS=1
               orr r1,#4（[r2,#3344] = SCB_SCR）      ← SLEEPDEEP=1
               dsb sy → wfi
               ... str 16MHz 的装载值 → bx lr          ← wfi 之后：6 条指令 / 14 字节，会执行

enter_standby:  bic r3,#1 → orr r3,#2                  ← LPDS=0、PDDS=1
                orr r1,#4                               ← SLEEPDEEP=1
                dsb sy → wfi
                ... bl reset_cause_decode → pop         ← wfi 之后：7 条指令 / 18 字节，永不执行
```

`wfi` 之后剩多少条指令，就是三档的本质：**Sleep 直接返回；Stop 的那一段会执行（所以重配时钟的代码写在这里才有地方放）；Standby 的那一段永远不会执行**：编译器照样生成了它，18 个字节静静躺在 Flash 里。这一条是"醒来是复位而不是继续"最硬的机器层证据，也是本章为什么反复强调"状态要放备份域"：`enter_standby()` 里 `wfi` 之后那半截代码，包括它准备读复位标志的那条 `ldr`，一句都不会跑。

另外三处对账值得看一眼：

- `dsb sy`（`f3bf 8f4f`）与 `wfi`（`bf30`）在三档里都是**相邻两条**，中间没插任何指令，脚本用"上一条正则接下一条正则"断言相邻，不是简单两个 `grep`；
- `SCB->SCR` 在机身里是 `[r2, #3344]`，`r2 = 0xE000E000`，`3344 = 0xD10`，objdump 自己把偏移还原出来了。内核外设和芯片外设不是一张地址图，S2 里已经遇见过一次（`0xE000E000` 那个 SysTick）；同理 `enter_standby` 里读复位标志编成 `[r3, #2164]` 而 `r3 = 0x40023000`：源码写的 `RCC_BASE(0x40023800) + 0x74` 被编译器合成成一个偏移，`0x40023000 + 0x874 = 0x40023874`，**base 是源码里的口径，机身里只有 base+偏移那一个数**，所以对地址要像第 2 步那样从两头拼，不能只信一边；
- `backup_domain_unlock()` 编出来是五个 `orr` 加一条 `ubfx`：`#268435456`(PWREN bit28) / `#256`(DBP bit8) / `#512`(BRE bit9) / `#262144`(BKPSRAMEN bit18) / `#32768`(RTCEN bit15)，最后 `ubfx r0, r0, #3, #1` 取的就是 `BRR` 那一位；`firmware_main` 里查 `WUF`/`SBF` 编成 `lsls r1, r3, #31` 与 `lsls r2, r2, #30` + `bpl`，**把标志位搬到符号位再决定跳不跳**，和 [S2](02-rcc-clock.md) 等 `HSERDY` 那一段用的是同一招。

## 附录：工程完整源码

不用跳 GitHub，整个 `main.c`、离线探针和取证脚本都在下面，滚动即达：

<<< ../../code/stm32/14-pwr/main.c

<<< ../../code/stm32/14-pwr/probe.c

<<< ../../code/stm32/14-pwr/probe.sh

PWR/BKPSRAM/RTC 的位定义与地址一律对照 CMSIS（本站 `.trellis/ref/cmsis/`），第 2 步就是那场对账；电流实测见 [E06](../lab/e06-lowpower-current.md)。

## 记忆锚点

::: tip 一句话记住
**Sleep 停脑，Stop 停钟（记忆在），Standby 断电（只留遗言）；唤醒源睡前配，醒来先查钟。**
:::

**延伸**：低功耗三档对比动画见 [S14 动画](/anim/stm32-pwr-three-modes.svg)；Stop 模式唤醒后时钟恢复在 [S2 RCC](02-rcc-clock.md) 有完整流程；ESP32 睡眠矩阵对照见 [P11](../esp32/11-lowpower.md)。

## 实物实验

- [E06 功耗实测](../lab/e06-lowpower-current.md)：三种模式电流逐一记录，算出"1 节 CR2032 能活多久"的估算表。

## 常见坑

- **Stop 唤醒后忘重配时钟**：系统跑在 HSI 16MHz，定时全慢 10 倍，唤醒后第一件事恢复 PLL。慢多少不是"大概"：`systick_period_us10` 实测，带着 168MHz 的装载值 `167999` 回 16MHz，周期从 1000 µs 变成 **10500 µs**。
- **只重配 SysTick，不重配 USART**：第三节那笔账，`BRR=729` 是按 PCLK2=84MHz 算的，PCLK2 掉回 8MHz 后同一个 729 打出 **10973 baud**（差 5%），波特率寄存器也是"随时钟走"的账，醒来一起重算（应得 `BRR=69`）。
- **开备份域只想到 DBP，漏了 BRE**：DBP（`PWR_CR` bit8）是写保护开关，备份 SRAM 的**供电**开关是 `PWR_CSR.BRE`（bit9），两个东西、两个寄存器。探针实测：有 DBP、无 BRE 时 `bkp_store()` 返回 **−2**，写进去的内容数组里仍是 0，看着写成功，其实是空气。
- **等备份域就绪却等错标志**：`backup_domain_unlock()` 的回执是 `BRR`（bit3），不是 `BRE`。第一遍读到 1（还没就绪）、置上 `BRR` 后第二遍才 0，睡前不等这一位，遗言就在断电前丢了。
- **把 `EWUP` 当"RTC 唤醒开关"**：`EWUP` 只管 PA0/EXTI **线 0**。RTC 闹钟是 EXTI 线 **17**、RTC 唤醒是 **18**，得走 `EXTI_IMR`。探针实测：只配 `EWUP` 再去查 17 号线 → **−1**，照样睡死。
- **IWDG 分频按"2 的幂续上去"想当然**：`PR` 是 8 个码但只有 7 档分频，`PR=6` 与 `PR=7` **同为 /256**。按 /512 算，`RLR=4095` 的最长超时从 **32760 ms** 被高估成 65520 ms——你以为狗还能撑一分多钟，它半分钟就咬。
- **调试器插着测电流**：SWD 连接让 Stop 电流虚高一个数量级，测功耗时拔掉仿真器，并把 `DBGMCU_CR` 的低三位清掉（固件里那一笔编出来是 `bic.w r3, r3, #7`）。
- **GPIO 悬空耗电**：悬空输入在漏电流上"喝电"，睡前全配模拟输入或确定上下拉。
- **Standby 后找变量**：SRAM 已清空，"睡前变量"必须用备份寄存器/备份 SRAM。`enter_standby()` 里 `wfi` 之后那 18 个字节，编译器生成了、Flash 里躺着、一句不会跑。
- **IWDG 在 Stop 里还在数**：超时就是 IWDG 复位，不是"醒来"，睡前算好超时或关 IWDG。
- **读完复位原因不清 `RMVF`**：`RCC_CSR` 那七个标志不清，下一次开机照抄这一次的结论（第五节表）。

## 短自测

1. Stop 和 Standby 醒来的"到哪"有什么本质区别？为什么 Standby 后变量全丢？
<details><summary>参考答案</summary>Stop 醒来回到 WFI 的下一条指令（继续跑），SRAM 与寄存器都保留，只是时钟停了得重配。Standby 醒来回到**复位入口**（像重新上电），因为调压器关了、1.2V 域断电、SRAM 内容全失。Standby 后变量全丢正是因为 SRAM 没有供电保留，只有备份域（备份寄存器+备份 SRAM）还活着，要留状态就得睡前写进备份域。</details>

2. 为什么 Stop 唤醒后系统时钟是 HSI 16MHz 而不是 168MHz？醒来后第一件事该做什么？
<details><summary>参考答案</summary>Stop 期间 1.2V 域时钟全停，包括 PLL（PLL 靠 HSE/HSI 倍频，停了就不出 168MHz）。醒来硬件自动启 HSI 作为系统时钟（保证最低能跑），但 PLL 没自动重启。第一件事是调 SystemClock_Config 重新配 PLL 切回 168MHz，否则所有定时器、UART 波特率都按 16MHz 算，全错 10 倍。</details>

3. 怎么在复位后区分"真上电"和"刚从 Standby 醒来"？
<details><summary>参考答案</summary>查 PWR_CSR.SBF（bit1，Standby Flag）。硬件在 Standby 唤醒时置 SBF，上电时 SBF=0。读 SBF=1 就是"刚从 Standby 醒来"，可以从备份 SRAM 捡回遗言；读 SBF=0 就是真上电。处理后写 PWR_CR.CSBF 清标志，避免下次上电误判。</details>

4. LSI 和 LSE 给 RTC 用，精度与续航怎么取舍？
<details><summary>参考答案</summary>LSE（外部 32.768kHz 晶振）精度高（±20ppm）、功耗极低，是 RTC 标配，长期定时（日历、闹钟）必须用它。LSI（内部 RC，约 32kHz）省一个外部晶振、BOM 成本低，但精度差（±5%）且随温度漂，短时周期唤醒（"每 2 秒醒一次"）够用，长期累计会偏。续航上两者都很省（µA 级），主要差别是精度而非功耗。</details>

5. 测 Stop 电流时为什么要拔掉 ST-Link？
<details><summary>参考答案</summary>ST-Link 通过 SWD 连着芯片，DBGMCU->CR 的 DBG_STOP 位若置着，Stop 下调试器还维持着调试接口的供电与时钟，电流虚高一个数量级。即便清了 DBG_STOP，SWD 物理连接本身的漏电也会引入误差。测真实 Stop 电流必须拔掉仿真器、清 DBG_STOP/DBG_STANDBY，让芯片真正"独自睡眠"。</details>

下面这三轮直接用本机 `probe.sh` 的实跑数提问：三档定出的寄存器字、醒来漏算的那笔账、看门狗最长能撑多久。

<QuizBank chapter="s14-pwr" />

## 对照表：本章概念 → 仓库与上游落点

| 概念 | 落点 |
|---|---|
| PWR_CR/CSR 全部位号（LPDS/PDDS/CWUF/CSBF/DBP/FPDS/VOS/WUF/SBF/BRE/BRR/EWUP） | CMSIS `stm32f407xx.h`（本站 `.trellis/ref/cmsis/`）；与 `_Pos` 的逐条对账 = `probe.sh` 第 2 步 |
| `SCB->SCR.SLEEPDEEP` | CMSIS-Core `core_cm4.h`（bit2 @ `0xE000ED10`）；地址同表对账 |
| 三档定档写出的那两个位 | `probe.c` §1 → 第三节 |
| 醒来时钟账（SysTick 周期、USART `BRR`） | `systick_period_us10` / `usart_baud_from_brr`，`probe.c` §3 → 第三节 |
| IWDG 八码七分频与超时区间 | `iwdg_pr_div` / `iwdg_timeout_ms`，`probe.c` §4 → 第六节 |
| 备份域四种回执与 `BRR` 两遍解锁 | `bkp_store` / `backup_domain_unlock`，`probe.c` §5 → 第五节 |
| 唤醒源矩阵（`EWUP` / `EXTI_IMR`） | `wake_source_armed`，`probe.c` §6 → 第四节 |
| 复位原因七标志解码 | `reset_cause_decode`，`probe.c` §7 → 第五节 |
| 三档机身与 `wfi` 之后的指令数 | `probe.sh` 第 3 步（`arm-none-eabi-gcc -O2 -c` + `objdump -d`）→ 第八节 |
| 备份 SRAM 4KB @ `0x40024000`、RTC 基址、`DBGMCU_CR` | `probe.sh` 第 2 步地址表（10 个地址现场重拼） |
| RTC 闹钟/唤醒的 EXTI 线号路由 | [S4 EXTI](04-nvic-exti.md) |
| 三档电流实测 | [E06 低功耗电流实测](../lab/e06-lowpower-current.md) |
| PLL 重配函数 | [S2 RCC](02-rcc-clock.md) SystemClock_Config |

## 你做到了

- 低功耗从"省电模式"三个字变成可设计、可测量、可核算的工程；
- 电池产品的续航估算有了第一性原理。

<div class="achievement">
✅ 下一站：<a href="15-spl-anatomy.html">S15 SPL 库解剖</a>：拆开标准库，看它怎样把我们手写过的每一行包进函数。
</div>

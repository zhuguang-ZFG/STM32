---
title: "低功耗设计"
platforms: [f407, f103, esp32]
---

# 低功耗设计

低功耗不是把芯片塞进一个 `WFI` 就结束。三档睡眠的硬件差别只有两个位，醒来后的时钟、备份域、唤醒线号和电流口径才是让电池预算成立的部分。本章把 F103、F407 与 ESP32 放在同一张账上：先定档，再算唤醒路径与时钟重建，最后用测量方法学判断一个 µA 数字能不能信。

三个来源都没有留下上板电流读数。正文把 DS5319 表 16/26 手册值（来源转引）、按公式推出来的续航账、来源的自述与待做实验分开写；F407 的 Stop 电流只给量级并标待复核，ESP32 的 RTC 内存容量按型号留待 TRM 核对。

## 本章罗盘

- **问题**：三档睡眠到底由哪两个位定档，为什么 `LPDS`、`FPDS`、`VOS` 不是档位开关？Stop 醒来为什么必须重配 PLL，F103 的 8 MHz 与 F407 的 16 MHz 各自要恢复什么？RTC 闹钟、RTC 唤醒定时器、USB 唤醒在 F407 上分别是哪条 EXTI 线，为什么把线 18 当 RTC 唤醒会睡死？备份域为什么必须按 `DBP → BDRST → 写 → 清 DBP` 的顺序，F103 与 F407 的备份存储差在哪？DS5319 的 14 µA、2 µA 与 1.4 µA 各是什么条件，F407 为什么只能写量级？0.11 mA 与 90 天为什么不自洽，DT830D 的 200 µA 档又为什么测不到 µs 级唤醒电流？
- **交付**：能按 `SLEEPDEEP` 与 `PDDS` 写出三档进入序列；能按 `VOS[15:14]=0b11` 配置 168 MHz，并说清只置 bit14 的写法为什么只到 120 MHz；能列出 F103/F407 的 Stop 恢复步骤并重算 BRR、SysTick、TIM；能画出 WKUP、PVD、RTC 闹钟与 RTC 唤醒定时器的线号；能按备份域顺序写 BKP 或 BKPSRAM；能读 DS5319 的电流表并标出条件；能用 DT830D 的 200 µA 档做静态电流测量，并说明它测不了什么；能用正向与反向两种算法检查续航。
- **边界**：三平台章。F103 的数字来自 DS5319 表 16/26（来源转引）与根书第 16 章；F407 的寄存器映射来自 S14 与 RM0090；ESP32 的睡眠模型来自 P11 与 IDF 文档。三个来源都没有上板电流记录，E06 仍是 `code_status: planned`、`hardware_status: pending`。本章不把 F407 的 VOS、FPDS、BKPSRAM 写成 STM32 通用，也不把 ESP32 的 Light/Deep 硬对齐成 STM32 三档。看门狗与复位证据留给[第 19 章][ch19]，调试与测量工具的分工留给[第 20 章][ch20]。
- **依据锚点**：根书第 16 章《低功耗设计》（`docs/16-低功耗设计.md`）、S14《低功耗：三种睡眠的唤醒与代价》（`mcu/docs/stm32/14-pwr.md`）、P11《低功耗：睡眠矩阵与 ULP》（`mcu/docs/esp32/11-lowpower.md`）、E06《低功耗电流实测》（`mcu/docs/lab/e06-lowpower-current.md`）；DS5319 表 16/26、RM0008 的 PWR/RCC/EXTI 章、RM0090 的 PWR/RTC/EXTI 章均转引自上述来源。[第 11 章](../v1-drivers/11-systick-timebase-rtc.md)的 RTC 与备份域、[第 13 章](../v1-drivers/13-uart-framed-protocol.md)的 BRR、[第 10 章](../v1-drivers/10-interrupts-nvic-exti.md)的 EXTI/NVIC 是本章的回链。

## 先做出来

先不接电流表，把三笔账在纸上对完。

1. **定档账**：读 `SCB->SCR` 的 bit2 与 `PWR_CR` 的 bit1。Sleep 是 0/0，Stop 是 1/0，Standby 是 1/1。三个组合之外没有第四种“省电模式”。
2. **时钟账**：Stop 醒来停在 HSI。F103 是 8 MHz，`BRR=0x271` 此时对应 12800；F407 是 16 MHz，`BRR=729` 此时对应 10973。先恢复 PLL，再谈串口。
3. **唤醒账**：WKUP 是线 0，PVD 是线 16，RTC 闹钟是线 17，RTC 唤醒定时器在 F407 上是线 22，USB OTG FS 唤醒是线 18。把 18 当 RTC 唤醒，睡下去就等不到闹钟。

来源工程 `mcu/code/stm32/14-pwr` 的 `probe.sh` 在宿主机上把固件函数接到假寄存器，报告 274/274 条断言通过，并用 CMSIS 头文件逐条对位号与地址。这是实测记录，但测的是代码写出的位和头文件常数，不是硅片电流；本章引用它时标“宿主假寄存器”，不把它当板上证据。

## 机制

### 一、三档只由两个位定档

F103 与 F407 的 Sleep、Stop、Standby 由两个位组合决定：内核侧的 `SCB->SCR.SLEEPDEEP`（地址 `0xE000ED10`，bit2）和电源侧的 `PWR_CR.PDDS`（`PWR` 基址 `0x40007000`，bit1）。Sleep 两位都清；Stop 是 `SLEEPDEEP=1`、`PDDS=0`；Standby 是两位都置 1。

| 档位 | SLEEPDEEP | PDDS | 醒来后 | 保留 |
| --- | --- | --- | --- | --- |
| Sleep | 0 | 0 | WFI 下一条 | SRAM、寄存器、外设时钟 |
| Stop | 1 | 0 | WFI 下一条，HSI 接管 | SRAM、寄存器；PLL 停 |
| Standby | 1 | 1 | 复位向量 | 只留备份域 |

`PDDS` 在 Sleep 下不参与定档，表里写 0 是为了给出完整字；不要把“`PDDS=0`”当成 Stop 的充要条件。`LPDS`（bit0）只选 Stop 下的稳压器档位，`FPDS`（bit9，仅 F407）只让 Flash 在 Stop 下掉电，`VOS[15:14]`（仅 F407）只决定最高主频与稳压器档位。三者都不改变“停在哪一档”。

```c
/* 进入前先开 PWR 时钟：RCC_APB1ENR.PWREN（bit28） */
SCB->SCR &= ~SCB_SCR_SLEEPDEEP_Msk;   /* Sleep：两位都清 */
PWR->CR  &= ~PWR_CR_PDDS_Msk;
__WFI();

SCB->SCR |= SCB_SCR_SLEEPDEEP_Msk;    /* Stop：SLEEPDEEP=1, PDDS=0 */
PWR->CR  &= ~PWR_CR_PDDS_Msk;
PWR->CR  |= PWR_CR_LPDS_Msk;          /* 可选：Stop 下低功耗稳压器 */
__WFI();

SCB->SCR |= SCB_SCR_SLEEPDEEP_Msk;    /* Standby：SLEEPDEEP=1, PDDS=1 */
PWR->CR  |= PWR_CR_PDDS_Msk;
__WFI();                              /* 不返回 */
```

`WFI` 是请求，不是保证。中断被 `PRIMASK` 屏蔽、当前优先级不够，或者唤醒标志已经挂着，都可能不睡或刚睡就醒。睡前清 EXTI 的挂起位（`EXTI->PR` 写 1 清），确认 NVIC 通道已使能；`WFE` 走事件，`SEVONPEND` 可以把挂起事件变成唤醒事件。

调试器连着时，`DBGMCU_CR` 的低三位（`DBG_SLEEP`、`DBG_STOP`、`DBG_STANDBY`）会让对应模式下的时钟继续跑，电流虚高。测电流时拔掉探针，并把这三位清掉。

根书第 16 章的实验用 PA0 的 EXTI 下降沿唤醒 Stop；Standby 的 WKUP 是 PA0 的上升沿，由 `PWR_CSR.EWUP`（bit8）使能。前者是普通 EXTI 配置，后者是 WKUP 引脚专用路径，边沿与使能位置都不同，不能并排成同一套配置。

![Sleep、Stop、Standby 三档：停什么、留什么、谁唤醒、醒来到哪](/anim/stm32-pwr-three-modes.svg)

三档的差别只有 `SLEEPDEEP` 与 `PDDS` 两位；图中的电流与唤醒时间是示意，具体条件见后文电流表。

### 二、F407 的 VOS：168 MHz 的入场券

F103 没有 VOS，最高 72 MHz；F407 的 `PWR_CR` 多了 `VOS[15:14]`，它决定稳压器输出档位与允许的最高主频。

| `VOS[15:14]` | 档位 | 最高 HCLK |
| --- | --- | --- |
| `0b11` | Scale1 | 168 MHz |
| `0b10` | Scale2 | 144 MHz |
| `0b01` | Scale3 | 120 MHz |

要在 168 MHz 跑，VOS 两位必须写成 `0b11`。示例只动这两位，其他位保持原值：

```c
PWR->CR = (PWR->CR & ~(3U << 14)) | (3U << 14);  /* VOS[15:14] = 0b11 */
```

只置 bit14（bit15=0、bit14=1）的写法是 `0b01`，对应 Scale3，最高 120 MHz；把它当 168 MHz 的配置，PLL 一升到 168 MHz 就超出了该档允许的上限。资料里“VOS 写 0 对应 144 MHz”的说法也不对：144 MHz 是 `0b10`，不是 0。

改 VOS 后等 `PWR_CSR.VOSRDY` 就绪，再提高 PLL 频率；升频与降频的先后按 RM0090 的稳压器规则来。VOS 只影响运行与 Stop 下的稳压器档位，不参与三档定档。Stop 下还可以用 `LPDS` 把稳压器切到低功耗档，用 `FPDS` 让 Flash 掉电；两者是省电选项，不是第四种睡眠模式。

![F407 低功耗三档与 PWR 寄存器落点](/figures/stm32-14-pwr.svg)

F407 的 `PWR_CR`/`PWR_CSR` 位图与三档落点；VOS 是 `[15:14]` 两位，不是 bit14 一位。

### 三、唤醒映射：EXTI 线号与 EWUP

唤醒源在线路层的落点比模式位更容易记错。F407 上要分清五条线：

| 唤醒源 | F103 | F407 | 使能位置 |
| --- | --- | --- | --- |
| WKUP 引脚 PA0 | EXTI0 | EXTI0 | `PWR_CSR.EWUP`（bit8），不进 `EXTI_IMR` |
| PVD | EXTI16 | EXTI16 | `EXTI_IMR` + NVIC |
| RTC 闹钟 | EXTI17 | EXTI17 | `EXTI_IMR` + NVIC |
| RTC 唤醒定时器 | 无 | EXTI22 | `EXTI_IMR` + NVIC |
| USB OTG FS 唤醒 | EXTI18 | EXTI18 | `EXTI_IMR` + NVIC |

`EWUP` 只管 PA0/线 0；把它当“深度睡眠唤醒总开关”，RTC 闹钟不会醒。RTC 闹钟是线 17；F407 的 RTC 唤醒定时器是线 22。线 18 是 USB OTG FS 唤醒，不是 RTC 唤醒。S14 的正文与 `mcu/code/stm32/14-pwr/main.c:119` 里把 RTC 唤醒写成线 18，这是错的，本章不沿用；按线 18 去配，RTC 到点也不会叫醒芯片。

Stop 的 EXTI 唤醒可以走中断，也可以走事件：`WFI` 要求 NVIC 通道使能，`WFE` 可以用 `EXTI_EMR` 的事件配置。无论哪条路，睡前都要清 `EXTI->PR` 的旧挂起位，否则刚睡下就被上一次的边沿叫醒。PVD 的阈值与 EXTI16 配置见根书第 16 章；NVIC 的优先级与分组见[第 10 章](../v1-drivers/10-interrupts-nvic-exti.md)。

### 四、Stop 退出：PLL 不会自己回来

Stop 期间 HSE 与 PLL 停掉。醒来时硬件把 HSI 接到系统时钟：F103 是 8 MHz，F407 是 16 MHz。PLL 的倍频配置不会自动恢复；“醒来 PLL 自动回来”是错误说法。恢复顺序分两套，不能互抄。

| F103 恢复步骤 | 动作 | 关键值 |
| --- | --- | --- |
| 1 | HSI 8 MHz 已在跑，PLL 停 | 不要直接用 72 MHz 的外设参数 |
| 2 | 开 HSE，等 HSERDY | BluePill 8 MHz 晶振 |
| 3 | 配 PLL：HSE × 9 | 72 MHz |
| 4 | 开 PLL，等 PLLRDY | — |
| 5 | Flash latency = 2 WS | 72 MHz、3.3 V |
| 6 | SYSCLK 切 PLL，等 SWS | — |
| 7 | APB1 /2 = 36 MHz，APB2 /1 = 72 MHz | — |
| 8 | 重开外设时钟，重算 SysTick、BRR、TIM | 71999、`0x271`、PSC/ARR |

| F407 恢复步骤 | 动作 | 关键值 |
| --- | --- | --- |
| 1 | HSI 16 MHz 已在跑，PLL 停 | 不要直接用 168 MHz 的外设参数 |
| 2 | 开 HSE，等 HSERDY | 8 MHz 晶振 |
| 3 | 配 PLL：M=8、N=336、P=2、Q=7 | 168 MHz；Q 给 48 MHz USB |
| 4 | 开 PLL，等 PLLRDY | — |
| 5 | Flash latency = 5 WS | 168 MHz、3.3 V |
| 6 | SYSCLK 切 PLL，等 SWS | — |
| 7 | APB1 /4 = 42 MHz，APB2 /2 = 84 MHz | — |
| 8 | 重开外设时钟，重算 SysTick、BRR、TIM | 167999、729、PSC/ARR |

两套的分母不同：F103 的 HSI 是 8 MHz、Flash 2 WS、APB1 36 MHz；F407 的 HSI 是 16 MHz、Flash 5 WS、APB1 42 MHz。把 F407 的 16 MHz 或 5 WS 抄到 F103，或者反过来，都会得到“看起来能跑、数全错”的结果。

串口是最先暴露问题的外设。F103 在 72 MHz 下 `BRR=0x271` 对应 115200；醒来停在 HSI 8 MHz 时同一个 `0x271` 对应 12800。F407 在 84 MHz 下 `BRR=729` 对应 115226（+0.023%）；PCLK2 掉到 8 MHz 后同一个 729 打出 10973，和 115200 相差约 90%，对端收到的是帧错。恢复 PLL 后要按新的 PCLK 重算 BRR，公式与帧格式见[第 13 章](../v1-drivers/13-uart-framed-protocol.md)。

`HAL_PWR_EnterSTOPMode`、SPL 的 `PWR_EnterSTOPMode` 只负责进 Stop，不替你恢复 PLL；HAL 的 `SystemClock_Config()` 或你自己的时钟初始化函数要在 `__WFI()` 返回后调用。HAL 时基若挂在 SysTick 上，先恢复 tick 再配时钟，避免时钟配置里的超时判断用错节拍。

![Stop 唤醒：HSI 8 MHz 装回 72 MHz 再开串口](/figures/sample-16-stop-wake.svg)

Stop 醒来先 HSI，再 HSE、PLL、Flash latency；不重配时 `0x271` 在 8 MHz 下是 12800。

### 五、备份域：DBP、BDRST、BRE/BRR

备份域是 Standby 与复位之后还在的那一小块：RTC、备份寄存器、F407 的 4 KB 备份 SRAM。它由 VBAT 续电，主电源掉电后仍能走。写它之前要先解锁，顺序不能省。

1. 开 PWR 时钟：`RCC_APB1ENR.PWREN`（bit28）；F103 还要 `BKPEN`（bit27）。
2. 置 `PWR_CR.DBP`（bit8），解除备份域写保护。
3. 需要复位整个备份域时，置 `RCC_BDCR.BDRST`（bit16），再清掉并等它归零。`BDRST` 会把 RTC 与备份寄存器一起复位，只在首次初始化用。
4. F407 还要置 `PWR_CSR.BRE`（bit9）开备份调压器，等 `PWR_CSR.BRR`（bit3）就绪。F103 没有这两位，不要照写。
5. 写 BKP 寄存器或 BKPSRAM。
6. 清 `PWR_CR.DBP`，恢复写保护。

```c
RCC->APB1ENR |= RCC_APB1ENR_PWREN;      /* F103 还要 |= RCC_APB1ENR_BKPEN */
PWR->CR |= PWR_CR_DBP;                  /* bit8：解锁备份域 */

RCC->BDCR |= RCC_BDCR_BDRST;            /* 首次初始化才做：复位备份域 */
RCC->BDCR &= ~RCC_BDCR_BDRST;
while (RCC->BDCR & RCC_BDCR_BDRST) { }

/* 下面两行只属于 F407：备份调压器使能与就绪 */
PWR->CSR |= PWR_CSR_BRE;                /* bit9 */
while (!(PWR->CSR & PWR_CSR_BRR)) { }   /* bit3：等就绪，不是等 BRE */

/* F103：BKP->DR1 = 0xA5A5;  F407：RTC->BKP0R = 0xA5A5 或写 BKPSRAM */
PWR->CR &= ~PWR_CR_DBP;                 /* 恢复写保护 */
```

| 平台 | 备份寄存器 | 备份 SRAM | 备注 |
| --- | --- | --- | --- |
| F103C8 | 10×16 bit = 20 B | 无 | `BKP_DR1` 到 `BKP_DR10`；42 个是大容量型号 |
| F407 | 20×32 bit = 80 B | 4 KB @ `0x40024000`，1024 words | `AHB1ENR` bit18 + DBP |

F407 的 4 KB 备份 SRAM 不是普通 SRAM：开 `RCC_AHB1ENR.BKPSRAMEN`（bit18）并置 DBP 才能写；写完一样清 DBP。F103 的 BKP 只有 10 个 16 位寄存器，别把 F407 的 20 个 32 位或 4 KB 抄过去。

备份域能扛复位与 Standby，但扛不住 VBAT 也掉电；没有纽扣电池时，拔掉主电源后备份域一样清空。RTC 的秒计数器、闹钟与备份寄存器的关系见[第 11 章](../v1-drivers/11-systick-timebase-rtc.md)；如果要把状态写进 Flash 而不是备份域，寿命与参数区规则见[第 17 章](../v1-drivers/17-flash-iap-ota.md)。

### 六、电流口径：手册值、板级值与量级

引用电流前先问四件事：谁在供电、时钟多少、温度多少、稳压器在哪一档。缺一个条件，数字就不可比。

| F103 项目 | 数值 | 条件 |
| --- | --- | --- |
| Sleep @72 MHz，外设全开 | 14.4 mA | 3.3 V、25 °C |
| Sleep @72 MHz，外设全关 | 5.5 mA | 3.3 V、25 °C |
| Stop，低功耗稳压器 | 14 µA | 3.3 V、25 °C、无 IWDG |
| Stop，主稳压器 | 24 µA | 同上 |
| Standby，LSI/IWDG/LSE/RTC 全关 | 2 µA | 3.3 V、25 °C |
| Standby，LSI 开 | 3.2 µA | 同上 |
| Standby，LSI+IWDG 开 | 3.4 µA | 同上 |
| VBAT，LSE+RTC | 1.4 µA | 备份域，不是整机 Standby |
| 唤醒 Sleep / Stop 主稳压器 / Stop 低功耗稳压器 / Standby | 1.8 / 3.6 / 5.4 / 50 µs | 见下 |
| PLL 锁定 | ≤200 µs | 不与唤醒时间相加 |

这些统一标为 DS5319 表 16/26 手册值（来源转引）。Stop 的 14 µA 不含 IWDG；开着 IWDG 时不能引用 14 µA。Stop 只有 14 µA 与 24 µA 两格，20 µA 不是本章引用的表值。Standby 的 2 µA 只在 LSI、IWDG、LSE、RTC 都关时成立；1.4 µA 是备份域，不是整机。唤醒时间同样分格：Sleep 1.8 µs、Stop 主稳压器 3.6 µs、Stop 低功耗稳压器 5.4 µs、Standby 50 µs；PLL 锁定最长 200 µs，不能把 5.4 与 200 相加叫成“唤醒时间”。

F407 的 Stop 电流只写“百 µA 量级（待复核）”。它比 F103 的 14 µA 高一个档，不能并排成同一量级。Standby 比 Stop 更低，具体值按 DS8626 的 Power consumption 表核对；在拿到带条件的表值之前，不要给具体数字，也不要用比 µA 更低的单位去描述它。

| 层级 | 包含 | 为什么表值对不上 |
| --- | --- | --- |
| 整板输入 | LDO、LED、USB-UART、传感器 | LDO 静态电流与 LED 常亮会盖过 µA |
| MCU 支路 | 3V3 到芯片 VDD | 调试器反向供电、SWD 漏电 |
| 芯片 VDD | 只算 MCU | DS 表值的条件在这里 |

板级读数不是芯片指标。测芯片支路要把调试器、LED、USB、传感器逐项断开；每断开一项记录差值，才知道电流归属。根书第 16 章的 `ch16-board-vs-chip` 图讲的就是这个边界。

![低功耗周期：Stop 底电流、唤醒峰值、活跃时间与平均电流](/figures/lowpower-current-evidence.svg)

底电流与峰值要和持续时间一起积分，才是平均电流；DS 典型值、开发板读数与裸芯片读数属于不同边界。

### 七、测量方法：DT830D 的 200 µA 档

E06 的 frontmatter 写明 `code_status: planned`、`hardware_status: pending`，实测记录表还是空的。下面所有读数都是待实测，不是已经量到的结论。

DT830D 的最低直流电流档是 200 µA，分辨率 0.1 µA，但最后一位会在底噪上跳几个字。更麻烦的是串入的采样电阻：满量程时它会产生约 0.2 V 的压降（按 1 kΩ 采样电阻估算，具体以表的手册为准），3.3 V 供电被拉到 3.1 V 附近，MCU 可能复位或进入欠压，读数自然不可信。

量程切换也有瞬态。从 mA 档换到 µA 档要断开电路，板子会掉电；自动量程表在切换瞬间同样会中断供电。正确做法是用排针或跳线帽做电流测量点，断电换档，再上电等读数稳定；活跃电流先用 mA 档，睡眠电流再换 µA 档，不要用 µA 档去测开机和射频突发。

万用表读的是平均值，不是峰值。唤醒时 µs 级的电流尖峰会被表头积分掉；要测唤醒电流，用 0.1 Ω 采样电阻加示波器，或用 PPK2、Joulescope 一类功耗分析仪。万用表适合回答“睡着后的底电流是多少”，不适合回答“醒来那 5 µs 里发生了什么”。

测量清单：

1. 拔掉调试器与 USB，断开 LED、传感器。
2. 测 3V3 或 VIN 的支路电流，记录电压与温度。
3. 先用 mA 档确认活跃电流，再断电换 µA 档。
4. 等读数稳定 10 s 以上，记录平均值与波动范围。
5. 每次只改一项（时钟、GPIO、外设、稳压器档位），记录差值。
6. 读数标“待实测”，不要写成芯片指标。

![DT830D 数字万用表：200 µA 档是最低直流电流档](/images/tools/multimeter-dt830d.jpg)

资料参考图，不是上板验证证据；DT830D 的 200 µA 档分辨率为 0.1 µA，但压降与底噪限制了它测动态电流的能力。

![E06 测电流接法：万用表串在电源正极与 VIN 之间](/images/labs/e06-current-meter.svg)

图中的算例数值是假设，用来演示公式，不是实测。

### 八、续航算术：0.11 mA 与 90 天

P11 给了一个周期上报的例子：活跃 200 mA 持续 2 s，Deep sleep 10 µA 持续 3598 s，1 小时一个周期。按同段模型算：

```text
一个周期的电荷 = 200 mA × 2 s + 0.01 mA × 3598 s
               = 400 mA·s + 35.98 mA·s
               = 435.98 mA·s
平均电流       = 435.98 mA·s / 3600 s
               = 0.1211 mA
```

220 mAh 的 CR2032 续航 = 220 / 0.1211 = 1817 h ≈ 76 天。P11 写“平均 0.11 mA、约 90 天”，这两个数不能同时成立。

| 算法 | 式子 | 结果 |
| --- | --- | --- |
| 正向：从占空比算平均 | (200×2 + 0.01×3598)/3600 | 0.1211 mA |
| 正向：220 mAh 续航 | 220/0.1211 | 1817 h ≈ 76 天 |
| 反向：0.11 mA 能撑多久 | 220/0.11 | 2000 h ≈ 83 天 |
| 反向：90 天需要多少平均电流 | 220/(90×24) | 0.102 mA |
| 容量反证：0.11 mA×90 天 | 0.11×2160 | 237.6 mAh > 220 mAh |

反向算暴露得更直接：90 天要 0.102 mA，0.11 mA 只够 83 天；按同段模型则是 0.121 mA、76 天。三个数字里只有 0.121 mA 与 76 天是同一条式子推出来的。0.68 mA 的两个例子反而自洽：220/0.68≈323 h≈13 天，2500/0.68≈3676 h≈153 天，P11 写 13 天与 150 天，量级对得上。

这些是文档推导，不是实测。实际续航还要扣 LDO 静态电流、电池自放电、温度对容量的影响、唤醒峰值与失败重试。把模型写成 `I_avg = Σ(I_k×t_k)/T`，每一项都带持续时间，才不会把底电流当成平均电流。

### 九、ESP32：最接近但不等价

ESP32 没有 STM32 的 Sleep、Stop、Standby 三档。它有 Light sleep 与 Deep sleep；Light 最接近 Stop，Deep 最接近 Standby，但都不是等价物。

| 维度 | Light sleep | Deep sleep | 对照 STM32 |
| --- | --- | --- | --- |
| CPU | 暂停 | 断电 | Light 接近 Stop；Deep 接近 Standby |
| RAM | 保持 | 数字域 RAM 断电 | Deep 醒来是复位 |
| 唤醒后 | 从暂停点继续 | 从复位向量重启 | Stop 继续；Standby 复位 |
| 电流 | 几 mA（来源说法，待核） | µA 级（来源说法，待核） | 条件不同，不能直接比 |
| 唤醒源 | GPIO、定时器、UART 等 | RTC 域：定时、EXT0、EXT1、触摸、UART、ULP | 与 STM32 EXTI 不是同一套 |

Deep sleep 的实质是复位：`esp_deep_sleep_start()` 不返回，醒来后 `app_main` 从头跑。普通全局变量在数字域 RAM 里，深睡后失电；能跨睡眠留下的只有四类属性：`RTC_DATA_ATTR`、`RTC_NOINIT_ATTR`、`RTC_SLOW_ATTR`、`RTC_FAST_ATTR`。它们都住在 RTC 域，但初始化和速度不同：`RTC_NOINIT_ATTR` 不初始化，冷启动读到的是脏值；`RTC_FAST_ATTR` 在 RTC fast memory，访问快但容量小。

| 属性 | 位置 | 跨 Deep sleep | 跨冷启动 |
| --- | --- | --- | --- |
| `RTC_DATA_ATTR` | RTC slow memory | 保持 | 初始化为设定值 |
| `RTC_NOINIT_ATTR` | RTC slow memory | 保持 | 不初始化 |
| `RTC_SLOW_ATTR` | RTC slow memory | 保持 | 初始化为设定值 |
| `RTC_FAST_ATTR` | RTC fast memory | 保持 | 初始化为设定值 |
| 普通全局 | 数字域 SRAM | 丢失 | 初始化为 0 |

P11 写 RTC slow memory“8 KB 量级”，但 classic ESP32 与 ESP32-S3 的 RTC 内存容量不同，ULP 程序也占这块空间；具体容量按型号 TRM 待核，本章不给一个跨型号的固定数。Light sleep 的“几 mA”同样是来源说法：Wi-Fi 开不开、RTC 内存保不保，都会改变读数。

唤醒源有五类：定时器、EXT0（单 RTC GPIO 电平）、EXT1（多 RTC GPIO 组合）、触摸、UART；ULP 也能把主核叫醒。Deep sleep 只认 RTC 域唤醒源，普通 GPIO 在数字域，断电后检测不了。醒来先用 `esp_sleep_get_wakeup_cause()` 分诊，再决定这一轮做什么。

![ESP32 睡眠矩阵：Light 保持 RAM，Deep 断电靠 RTC 域](/anim/esp32-sleep-matrix.svg)

Light 与 Deep 的差别在“RAM 保不保、醒来是继续还是复位”；与 STM32 三档最接近但不等价。

STM32 的 RTC 备份域与闹钟见[第 11 章](../v1-drivers/11-systick-timebase-rtc.md)；ESP32 的 NVS 与 OTA 不在本章范围。

## 测量与证据

本章的读数按来路分四类：宿主实跑的断言、手册或头文件的文档条目、按公式推出来的账、来源自述但没有记录的实验。下面的表逐项标出来路；没有一条是本章的上板电流读数。

### 读数来路表

| 取证项 | 来路 | 读数或结论 | 性质 |
| --- | --- | --- | --- |
| 三档定档 | `SCB->SCR.SLEEPDEEP` + `PWR_CR.PDDS`；S14 probe 第 1 节 | Sleep 0/0、Stop 1/0、Standby 1/1 | 手册规则 + 实测记录（宿主假寄存器） |
| F407 VOS | RM0090 的 PWR 章；S14 正文写法有误 | `0b11`=168、`0b10`=144、`0b01`=120 | 手册规则（来源错误已修正） |
| EXTI 线号 | RM0090 的 EXTI 章；S14 与 `main.c:119` 写 RTC 唤醒=18 | 闹钟 17、唤醒定时器 22、USB 18 | 手册规则（来源错误已修正） |
| F103 电流与唤醒 | DS5319 表 16/26，经根书第 16 章转引 | 14.4/5.5 mA、14/24 µA、2/3.2/3.4 µA、1.4 µA、1.8–5.4 µs、PLL≤200 µs | 手册值（来源转引） |
| F407 Stop 电流 | S14 正文 | 百 µA 量级 | 来源说法（未复核） |
| 备份域容量 | F103C8 10×16 bit；F407 20×32 bit + 4 KB | 20 B；80 B + 1024 words | 手册规则 |
| 0.1211 mA / 76 天 | 本章按 P11 同段模型复算 | 435.98 mA·s / 3600 s；220/0.1211 | 公式推导 |
| 0.11 mA / 90 天 | P11 续航段 | 与同段模型不自洽；0.11 mA 只够 83 天，90 天要 0.102 mA | 来源说法（未复核） |
| E06 读数 | frontmatter `code_status: planned`、`hardware_status: pending` | 记录表为空 | 待实测 |
| S14 probe | `sh probe.sh` 的宿主断言 | 274/274；位号 29 条、地址 10 个 | 实测记录（宿主假寄存器） |
| ESP32 Light sleep 电流 | P11 | 几 mA | 来源说法（待核） |
| ESP32 RTC 内存容量 | P11 | 8 KB 量级 | 来源说法（按型号 TRM 待核） |
| 板级与芯片边界 | 根书第 16 章、E06 | 整板 ⊃ MCU 支路 ⊃ 芯片 VDD | 文档条目/设计边界 |
| 万用表压降 | DT830D 200 µA 档，按 1 kΩ 估算 | 满量程约 0.2 V | 文档推导（具体以表手册为准） |

能互相对上的只有手册位、算术与静态代码：`0x271` 在 8 MHz 下算出 12800，729 在 8 MHz 下算出 10973，435.98/3600 算出 0.1211，220/0.1211 算出 76 天。它们都不能证明某块板上的 Stop 电流真的是 14 µA，也不能证明某次唤醒的 5.4 µs。要补上后者，得按下面的台架留下电流波形、电压与温度。

### 待做台架

1. F103 Stop 两格：同一块 BluePill，低功耗稳压器与主稳压器各测一次，拔掉调试器、LED、USB，记录 3.3 V 与温度。
2. F407 Stop/Standby：用 0.1 Ω 采样电阻加示波器看唤醒峰值，万用表看底电流；VOS 三档各记录一次。
3. 唤醒电流：PA0 边沿、ISR 入口 GPIO、时钟恢复后 GPIO 三路标记，配合电流波形对齐。
4. ESP32 Deep sleep：拔 USB、关 Wi-Fi、只留定时唤醒，记录底电流与唤醒原因；RTC 内存容量查对应型号 TRM。

这些台架都还没做。没有读数之前，本章只给判据与记录方法。

## 失败分支

| 现象 | 原因 | 区分证据 | 下一动作 |
| --- | --- | --- | --- |
| 进不了 Stop，电流仍是 mA | `SLEEPDEEP`/`PDDS` 写错，或 WFI 前中断被屏蔽 | 读回 SCR bit2、CR bit1；看 `PRIMASK` | 按两位组合重写；确认 NVIC 使能 |
| 刚睡下就醒 | EXTI 旧挂起位没清，或唤醒源一直在抖 | 读 `EXTI->PR`；屏蔽该线后不再醒 | 睡前写 1 清 PR；加消抖 |
| 醒来串口乱码 | 时钟停在 HSI，BRR 未重算 | 位宽 78.125 µs（12800）而不是 8.68 µs（115200） | 先恢复 PLL，再重算 BRR |
| SysTick 慢 8 倍或 10.5 倍 | LOAD 仍是 72/168 MHz 的值 | 读回 LOAD；量 1 ms 实际 8/10.5 ms | 按新 HCLK 重算 LOAD |
| 定时器周期全错 | PSC/ARR 按旧 PCLK 算 | 示波器量周期；读回 PSC/ARR | 重算 PSC/ARR，注意 APB 分频 |
| 备份寄存器写不进 | 没置 DBP，或 F407 没开 BRE、没等 BRR | 读回 BKP 值；看 DBP/BRE/BRR 位 | 按 DBP→BDRST→BRE/BRR→写→清 DBP 顺序 |
| 每次醒来 RTC 被清 | 每次初始化都拉 BDRST | 读 RTC 时间；看 BDRST 位 | BDRST 只在首次初始化用 |
| 168 MHz 上不去或不稳 | VOS 不是 `0b11`，或 Flash latency 不够 | 读 `PWR_CR[15:14]`；读 `FLASH_ACR` | 写 `0b11`、5 WS，再升 PLL |
| F407 电流比预期高 | 调试器、LED、USB、LDO、悬空 IO | 逐项断开，记录差值 | 拔探针、清 DBGMCU 低三位、GPIO 模拟输入 |
| 万用表 µA 档读数乱跳或板子复位 | 压降过大、底噪、量程切换瞬态 | 换 mA 档正常；µA 档电压跌落 | 断电换档；用采样电阻加示波器 |
| 电池寿命比算的短 | 平均电流漏算峰值、LDO、自放电 | 实测平均电流与模型对比 | 重算 `I_avg`；逐项掐电 |
| ESP32 深睡后变量丢 | 普通 RAM 失电 | 变量值变 0；`RTC_DATA_ATTR` 变量保持 | 换 `RTC_DATA_ATTR` 或 NVS |
| ESP32 深睡后代码继续跑 | 误以为 `esp_deep_sleep_start()` 会返回 | 串口打印复位原因；`app_main` 从头跑 | 按复位模型设计；用 wakeup cause 分诊 |
| RTC 定时唤醒不醒 | 配了线 18，或 `EXTI_IMR`/NVIC 没开 | 读 `EXTI_IMR` bit22；换线 17/22 测试 | 改线 22，开 NVIC，清 PR |

## 跨平台边界

同一个“进 Stop”在三颗芯片上的落点不同，代码不能平移。

| 维度 | F103 | F407 | ESP32 |
| --- | --- | --- | --- |
| 档位 | Sleep/Stop/Standby | 同左 + VOS/FPDS | Light/Deep |
| 定档位 | `SLEEPDEEP` + `PDDS` | 同左 | IDF sleep API |
| HSI | 8 MHz | 16 MHz | 无对应 |
| 最高主频 | 72 MHz | 168 MHz（VOS=`0b11`） | 型号相关 |
| Stop 电流 | 14/24 µA（DS5319） | 百 µA 量级（待复核） | Light 几 mA（待核） |
| 备份 | 10×16 bit BKP | 20×32 bit + 4 KB BKPSRAM | RTC memory |
| RTC 唤醒 | 闹钟 EXTI17 | 闹钟 17、定时器 22 | RTC timer |
| 醒来 | Stop 继续；Standby 复位 | 同左 | Deep 复位 |
| 测量 | 万用表加示波器 | 同左 | 同左，注意射频 |

F103 与 F407 的 HSI、Flash latency、APB 分频、VOS、备份容量都不同；F407 的 VOS、FPDS、BKPSRAM 不能写成“STM32 通用”。ESP32 的 Light/Deep 只是最接近 Stop/Standby，Deep 是复位，Light 也没有 STM32 Sleep 那种“只停 CPU、外设全活”的对应档。换芯片先查对应 RM/DS 的 PWR、RCC、EXTI 章，不要按另一颗芯片的位图改。

时钟树与 Flash 等待的细节见[第 8 章](../v1-drivers/08-architecture-memory-clock.md)；DMA 在 Stop 前也要关时钟，见[第 14 章](../v1-drivers/14-dma.md)；GPIO 睡眠电平与模拟输入见[第 9 章](../v1-drivers/09-gpio.md)。

## 离开检查

1. 三档睡眠由哪两位决定？`LPDS`、`FPDS`、`VOS` 各管什么？
2. F407 要跑 168 MHz，`VOS[15:14]` 写多少？只置 bit14 是多少 MHz？
3. RTC 闹钟、RTC 唤醒定时器、USB OTG FS 唤醒在 F407 上分别是哪条 EXTI 线？`EWUP` 管哪条？
4. Stop 醒来 F103 与 F407 的 HSI 各是多少？恢复序列里 Flash latency 与 APB1 分频各是多少？
5. `0x271` 在 8 MHz 下是多少 baud？729 在 8 MHz 下是多少？与 115200 差多少？
6. 备份域写入的顺序是什么？F103 与 F407 的备份存储各有多大？
7. 0.11 mA 与 90 天为什么不自洽？按 200 mA×2 s + 10 µA×3598 s 算，平均电流与 220 mAh 续航是多少？
8. 为什么 DT830D 的 200 µA 档测不到 µs 级唤醒电流？它适合测什么？
9. ESP32 Deep sleep 与 STM32 Standby 的最关键差别是什么？跨 Deep sleep 只能靠哪四类属性？

<details>
<summary>对照答案</summary>

1. 由 `SCB->SCR.SLEEPDEEP` 与 `PWR_CR.PDDS` 决定：Sleep 0/0，Stop 1/0，Standby 1/1。`LPDS` 选 Stop 下的稳压器档位，`FPDS` 让 Flash 在 Stop 下掉电，`VOS` 决定最高主频与稳压器档位；三者都不定档。
2. 写 `0b11`（Scale1）。只置 bit14 是 `0b01`（Scale3），最高 120 MHz；144 MHz 是 `0b10`。
3. RTC 闹钟是线 17，RTC 唤醒定时器是线 22，USB OTG FS 唤醒是线 18。`EWUP` 只管 PA0/线 0，不进 `EXTI_IMR`。
4. F103 的 HSI 是 8 MHz，Flash 2 WS，APB1 /2 = 36 MHz；F407 的 HSI 是 16 MHz，Flash 5 WS，APB1 /4 = 42 MHz。PLL 不会自动恢复。
5. `0x271`=625，`USARTDIV=39.0625`，8e6/(16×39.0625)=12800；729 在 8 MHz 下是 10973，与 115200 约差 90%。72 MHz 下 `0x271` 是 115200；84 MHz 下 729 是 115226（+0.023%）。
6. 开 PWR 时钟 → 置 DBP → 需要时拉 BDRST 再释放 → F407 置 BRE 并等 BRR → 写 BKP/BKPSRAM → 清 DBP。F103 是 10×16 bit（20 B）；F407 是 20×32 bit（80 B）加 4 KB BKPSRAM。
7. 435.98 mA·s / 3600 s = 0.1211 mA；220/0.1211 = 1817 h ≈ 76 天。0.11 mA 只够 83 天；90 天需要 0.102 mA；0.11 mA×2160 h = 237.6 mAh，已经超过 220 mAh。
8. 万用表读平均值，µs 级尖峰被积分掉；200 µA 档还有底噪与约 0.2 V 的压降。它适合测稳定后的底电流，不适合测唤醒峰值；峰值用采样电阻加示波器或功耗分析仪。
9. 两者醒来都是复位，但 ESP32 的 Deep sleep 把数字域整个断电，只留 RTC 域，`esp_deep_sleep_start()` 不返回；STM32 的 Standby 关主稳压器、保留备份域。跨 Deep sleep 只能用 `RTC_DATA_ATTR`、`RTC_NOINIT_ATTR`、`RTC_SLOW_ATTR`、`RTC_FAST_ATTR` 四类属性。

</details>

<QuizBank chapter="s14-pwr" />

[ch19]: ./19-watchdog-reset-hardfault.md
[ch20]: ./20-debug-performance.md

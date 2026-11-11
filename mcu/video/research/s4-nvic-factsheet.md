# S4 NVIC 事实表（v2 重制底稿）

来源：

- `.temp/v2-facts/s4-probe.log`（2026-10-29 本机实跑；宿主 gcc 16.1.0，交叉 arm-none-eabi-gcc 10.3.1）
- `code/stm32/04-nvic-exti/probe.sh`
- `docs/stm32/04-nvic-exti.md`（S4 正文口径）

## 一、常数现挖（每行自带 文件:行号）

- 外设链：PERIPH_BASE 0x40000000（stm32f407xx.h:910）→ APB2 +0x00010000（:928）→ SYSCFG +0x3800（:974）/ EXTI +0x3C00（:975）。
- 内核链：SCS_BASE 0xE000E000（core_cm4.h:1550）→ SysTick +0x0010（:1555）/ NVIC +0x0100（:1556）/ SCB +0x0D00（:1557）。
- 位号口径：NVIC_PRIO_BITS = 4（stm32f407xx.h:49）；PRIGROUP_Pos = 8（core_cm4.h:531）；AIRCR VECTKEY = 0x5FA（core_cm4.h:1661）；RCC_SYSCFGEN_Pos = 14（:10076）；EXTICR_EXTI0_PF = 0x0005（:11662）。
- EXTI 偏移：IMR 0x00 / EMR 0x04 / RTSR 0x08 / FTSR 0x0C / SWIER 0x10 / PR 0x14（stm32f407xx.h:444–449）；SYSCFG_EXTICR 起始偏移 0x08（:547）。

## 二、宿主断言（52/52）

- 编译期 `_Static_assert`：正文数字 vs 头文件提取值逐条对撞全过。
- 基址拼装：0x40010000 + 0x3800 = SYSCFG 0x40013800（+0x08 = EXTICR 0x40013808）；0x40010000 + 0x3C00 = EXTI 0x40013C00；PR = 0x40013C00 + 0x14 = 0x40013C14。
- IRQn → 槽 / ISER / IP（槽 = IRQn + 16，ISER 下标 = IRQn/32，位 = IRQn%32，IP 字节 = 0xE000E400 + IRQn）：

| 中断 | IRQn | 槽 | 槽偏移 | ISER | IP 字节 |
|---|---:|---:|---|---|---|
| SysTick | -1 | 15 | 0x003c | （SHP） | 0xE000ED23 |
| EXTI0 | 6 | 22 | 0x0058 | ISER0 bit6 | 0xE000E406 |
| EXTI1 | 7 | 23 | 0x005c | ISER0 bit7 | 0xE000E407 |
| EXTI9_5 | 23 | 39 | 0x009c | ISER0 bit23 | 0xE000E417 |
| TIM2 | 28 | 44 | 0x00b0 | ISER0 bit28 | 0xE000E41C |
| USART1 | 37 | 53 | 0x00d4 | ISER1 bit5 = 0xE000E104 | 0xE000E425 |
| EXTI15_10 | 40 | 56 | 0x00e0 | ISER1 bit8 | 0xE000E428 |

- 优先级编码：IP[IRQn] = (priority << 4) & 0xFF（core_cm4.h:1818）。0→0x00、1→0x10、5→0x50、10→0xA0、15→0xF0。
- 越界截断（同一个字节读回来是另一个合法值）：16→0x00 读回 0；17→0x10 读回 1；20→0x40 读回 4；255→0xF0 读回 15；256→0x00 读回 0。开场「你写 16，芯片收到 0」即此表第一行。
- AIRCR.PRIGROUP（位 [10:8]）八种切法：

| PRIGROUP | 抢占位 | 子优先级位 | 写法（VECTKEY\|组值<<8） |
|---:|---:|---:|---|
| 0–3 | 4 | 0 | 0x05FA0000–0x05FA0300 |
| 4 | 3 | 1 | 0x05FA0400 |
| 5 | 2 | 2 | 0x05FA0500 |
| 6 | 1 | 3 | 0x05FA0600 |
| 7 | 0 | 4 | 0x05FA0700 |

- SysTick 不在 NVIC->IP 里：走 SCB->SHP，实测地址 0xE000ED23（core_cm4.h:1814–1824）。
- EXTICR 选 F 口：线 0 写 0x00000005（字段 [3:0]）、线 1 写 0x00000050（[7:4]）、线 6 与线 10 都写 0x00000500（[11:8]，寄存器分别是 EXTICR2/EXTICR3）。

## 三、向量表与弱符号

- 直接数 startup_stm32f407xx.s 的 `.word` 行：98 项（16 内核 + 82 外设）；7 个 IRQn 回验全中（见上表槽号）。
- `.isr_vector` 大小 0x188 = 392 字节 = 98 × 4，落在 0x08000000；`.text` 紧随其后 0x84 字节 @ 0x08000188。
- 真链接顶替：`EXTI0_IRQHandler` 是强符号 0x08000188（不再 weak）；`Default_Handler` 0x08000204；槽 22 内容 = 0x08000189 —— 最低位 1 是 Thumb 位。
- EXTI0_IRQHandler 反汇编：800018c movs r1,#1；800018e str.w r1,[r3,#3092]（0xC14，基址 0x40013000 → EXTI->PR，进门先清挂起）；8000192 ldr r3,[r2,#0]；8000194 add r3,r1；8000196 str r3,[r2,#0]（计数器 @0x20000000）；8000198 bx lr；字面量池 0x40013000 / 0x20000000。

## 四、口径边界

- IRQn -3 / -2 / -1（Reset / NMI / HardFault）的固定优先级来自 ARM 架构手册（PM0214），不在本集数字表里；本集只讲可编程的 4 位优先级字段。
- 槽号 -13 在枚举里被作者跳过（MemoryManagement -12 与 BusFault -11 之间），视频按头文件实际值讲。

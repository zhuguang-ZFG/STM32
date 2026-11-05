---
title: GD32 双系路线
---

# GD32 路线：一颗国产芯的两条进化线

> 🎯 检验你有没有学透一颗芯片，最快的办法是换一颗”长得像但不一样”的：GD32 给你两条线：G 篇逐字段对照 STM32F407（同名不同姓），V 篇用你已经会的知识丈量 RISC-V。

![GD32 路线总览：G 篇对照 + V 篇 RISC-V 双线并行](/anim/gd32-roadmap.svg)

兆易创新 GD32 是国内出货量最大的 MCU 家族之一，也是"学透一颗再举一反三"的最佳教材。这条路线一次讲两条线：

- **G 篇（GD32F4xx，ARM Cortex-M4F）**：STM32F407 的"近亲"——寄存器布局神似，但外设库叫 **RCU** 不叫 RCC、主频更高（**F450 200MHz / F470 240MHz**，官方库默认档就是 200MHz），USART 等外设还有增强点。逐字段对照学"兼容但不相同"。
- **V 篇（GD32VF103，RISC-V RV32IMAC）**：Bumblebee 内核 108MHz：没有 NVIC、没有 SysTick，中断走 **CLIC**、内核定时走 **MTIME**。用你已经会的 STM32 知识丈量 RISC-V，只讲迁移必需的四件事。

事实基准：**官方固件库 + 官方手册双层核对**——固件库取 GD32F4xx **V3.3.3** / GD32VF103 官方库（源码按版本核对），手册取 **GD32F4xx User Manual Rev3.0**、**GD32VF103 User Manual EN V1.0**、**GD32F407xx Datasheet Rev2.7**、**GD32F470 Product Brief**、**Bumblebee Core Brief**（参考缓存位于 .trellis/ref/，不随仓库分发）。位域、引脚与复用号已按"头文件说什么 + 手册怎么写"逐项标注出处；手册本身留白或没给的（典型如 Flash"频率↔等待周期"对照表、VF103 的 CKOUT0 引脚名），页面明写**手册留白**并降级为"待上板实测"，**不猜、不外推**。

## G 篇：GD32F4xx 对照篇

| 章 | 标题 | 带走什么 |
|---|---|---|
| **[G0 环境与工具链](/gd32/00-env.md)【成稿】** | 官方库 V3.3.3 目录解剖 | 复用 xPack ARM GCC，启动文件/system/链接脚本三件套 |
| **[G1 RCU 时钟树：200MHz 是怎么算出来的](/gd32/01-rcu-clock.md)【成稿】** | 与 S2 逐字段对照 | PLL 同布局更激进（400MHz VCO）、电压档三件套带 HDRF/HDSRF 回执、FMC_WS"官方留白"的真相（datasheet 零等待）、USB 为什么不能走 PLLQ、CK_OUT0 理论 50MHz |
| **[G2 GPIO 与 AF 复用对照](/gd32/02-gpio-af.md)【成稿】** | 七大寄存器"同名不同姓"点名 | 多出 BC/TG 两件兵器，编码逐位核对，速度四档按负载的实测上限（datasheet Table 4-28） |
| **[G3 USART 增强点](/gd32/03-usart.md)【成稿】** | 从 `gd32f4xx_usart.h` 比出的差异清单 | 8 个串口、CTL0/1/2 命名差异、CLEN/SCEN/NKEN 增强点已核验 |
| **[G4 GD32 外设差异](/gd32/04-periph-diff.md)【成稿】** | USBHS/EXMC/CAN/ENET/SDIO 逐项"有没有、一不一样" | GD32 独有外设与 STM32 对照；CAN 位时序连复位值都一样、SDIO 分频多一位（藏在 bit31）、ULPI 12 根引脚同脚同 AF |

## V 篇：GD32VF103 RISC-V 篇

| 章 | 标题 | 带走什么 |
|---|---|---|
| **[V0 RISC-V 工具链与启动](/gd32/05-riscv-toolchain.md)【成稿】** | riscv-none-elf-gcc、启动文件与链接脚本的 RISC-V 版 | 三元组+march/mabi，无 FPU/CPACR，sp 软件设 |
| **[V1 Bumblebee 内核与 CLIC 中断](/gd32/06-clic-irq.md)【成稿】** | 没有 NVIC 的世界：向量直跳 | ECLIC 两维优先级、shv 向量模式、MTIME 取代 SysTick |
| **[V2 RCU 与 108MHz](/gd32/07-rcu-108m.md)【成稿】** | G 篇知识平移（预设档 48/72/108M） | 25M 绕 PLL1 两圈、乘数全家福、回读对账 |
| **[V3 MTIME 与裸机延时](/gd32/08-mtime-delay.md)【成稿】** | 替代 SysTick 的内核时基 | 64 位读写纪律、主频除四、查询式 delay_ms |
| **[V4 GPIO 最小系统](/gd32/09-gpio-minimal.md)【成稿】** | 第一个 RISC-V 点灯闭环 | F1 血统 AFIO、四位一坑、工程拼图收官 |

## 当前状态

规划清单已登记到 docs/curriculum.json，未建页面不生成死链接，一手源码已入库核实，章节成稿与动画按批次推进；板卡接线节待指定基准板后回填。

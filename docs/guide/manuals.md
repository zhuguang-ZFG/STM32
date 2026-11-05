---
title: 导读·手册地图
---

# 手册地图：官方资料的正确打开方式

> 🎯 高手和新手查资料的区别：新手搜"STM32 GPIO 怎么配"，高手翻 RM0090 §8。二手教程会过时、会抄错，**手册才是最终裁决**——这页教你认门。

这页讲"翻哪本"；**翻的是哪一版、论文的 DOI、被逐行引用的代码固定在哪个 tag**，全在 [参考文献](../reference/bibliography.md)；章节末尾的 `[D2]` 标签就指向那里。

## STM32 侧（ST 官方，st.com 搜编号即得）

| 手册 | 它管什么 | 什么时候翻 |
|---|---|---|
| **RM0090**（参考手册） | F405/407 全部外设寄存器的逐位定义 | 写任何外设代码时的"字典"；S 篇每章都引用它的章节号 |
| **STM32F407ZG Datasheet**（数据手册） | 引脚定义、复用功能表、电气参数、封装 | 选引脚、查复用（AF 几）、看电压电流限额时 |
| **PM0214**（Cortex-M4 编程手册） | 内核寄存器（NVIC/SysTick/SCB）、异常模型、指令集摘要 | [S4 中断](../stm32/04-nvic-exti.md)、[S5 SysTick](../stm32/05-systick.md)、[S16 HardFault](../stm32/16-debug-hardfault.md) |
| ARMv7-M 架构参考手册 | 指令集的完整定义 | 读启动文件/上下文切换汇编时（B4、F2） |
| [野火霸天虎资料页](https://doc.embedfire.com/products/link/zh/latest/mcu/stm32/stm32f407_batianhu.html)（doc.embedfire.com） | **这块板**的原理图、引脚分配、外设接线 | 用板载 RGB/按键/扩展接口之前必查 |

::: tip RM0090 怎么用
不要从头读！按"章节目录 → 外设 → 寄存器地图 → 具体寄存器位"的路径查。每个外设章节末尾都有 register map 汇总表，配合正文位定义使用。
:::

## ESP32 侧（乐鑫官方，docs.espressif.com）

| 手册 | 它管什么 | 什么时候翻 |
|---|---|---|
| **ESP32-S3 技术参考手册（TRM）** | S3 全部外设寄存器、IO_MUX/GPIO Matrix、系统结构 | [P2 GPIO 矩阵](../esp32/02-gpio-matrix.md) 等底层章节 |
| **ESP-IDF 编程指南**（选 v5.5 + ESP32-S3） | API 参考、驱动用法、构建系统、启动流程 | P 篇日常查阅；版本和芯片别选错 |
| **ESP32-S3-WROOM-1 Datasheet** | 模组引脚、电源要求、RF 参数 | 硬件设计/供电排查时 |
| [立创实战派 S3 wiki](https://wiki.lckfb.com/zh-hans/szpi-esp32s3/) | **这块板**的原理图、引脚分配、外设接线 | 用板载屏/麦克风/按键之前必查 |

## RTOS 侧

| 资料 | 它管什么 |
|---|---|
| FreeRTOS 内核源码（github.com/FreeRTOS/FreeRTOS-Kernel） | 一切疑问的最终答案——[F 篇](../rtos/index.md)逐文件带你读 |
| 《Mastering the FreeRTOS Real Time Kernel》（官方免费 PDF） | 概念与 API 的系统讲解 |
| RT-Thread 内核源码（github.com/RT-Thread/rt-thread）+ 官方文档中心 | [R 篇](../rtos/index.md)基准；内核编程指南章节尤其好 |
| 《RT-Thread 内核实现与应用开发实战指南》（野火，免费） | 从零造一个 RT-Thread 风格内核，配合 R 篇食用极佳 |

## C 与工具链

| 资料 | 用途 |
|---|---|
| C 标准草案 n1570（C11 免费版） | [C7 UB](../c/07-ub-misra.md) 的"呈堂证供" |
| AAPCS（ARM 过程调用标准） | [C6](../c/06-abi-stack.md) 的规则原文 |
| GNU ld 手册（sourceware.org） | [B3 链接脚本](../build/03-linker-script.md) 的语法大全 |
| 《程序员的自我修养——链接、装载与库》 | B 篇最佳中文伴侣书 |

## 记忆锚点

::: tip 一句话记住
**外设查 RM/TRM，引脚查 Datasheet，内核查 PM，API 查官方指南，实战查板厂 wiki**：五本各管一段，别张冠李戴。
:::

## 常见坑

- **手册版本错配**：RM0090 是 F405/407 的；拿 F103 的 RM0008 对 F407 寄存器，位定义能对上才怪。
- **IDF 文档忘选版本**：网页默认 latest，我们基准 v5.5.x；URL 里带版本号，别读错代的 API。
- **只收藏不下载**：关键手册（RM0090、datasheet、TRM）下载 PDF 到本地，标注书签；现场调试时网速靠不住。

## 你做到了

- 每类问题知道翻哪本、怎么查；
- 收藏夹从"100 篇二手教程"换成"5 本一手手册"。

---
title: 关于我们与致谢
---

# 关于我们与致谢

> 🎯 一个人的学习记录不值钱，值钱的是把它按别人能复现的方式摊开写。这就是本站存在的全部理由。

## 这个项目是什么

「通往单片机之路」是一份**寄存器级**的单片机教程：同一颗芯片，既讲手册怎么说，也讲源码怎么做，还讲示波器上看到什么。两条主线（STM32F407 裸机、ESP32-S3 + ESP-IDF）、两套 RTOS 精讲（FreeRTOS 内核源码级、RT-Thread 组件生态）、一条 GD32 双系对照线，全部实验在作者实持的板子上可复现。

它受[通往AGI之路](https://waytoagi.feishu.cn/)启发。从那里借来三件事：

| 借来的做法 | 本站的对应 |
|---|---|
| 开源、体系化、面向初学者 |  Apache-2.0 全开放；板块按依赖关系成体系，导览页先讲"这条路怎么走" |
| 一张不断更新的地图，而不是线性课程 | [首页学习地图](/)按成稿状态实时显示全站进度，读者按身份分流而不是从头滚到尾 |
| 名词解释与常见问题前置 | [术语速查](/reference/glossary.md) + [FAQ](/reference/faq.md)，卡住先查一句话版本 |

不借的一件事：**不把深度让渡给广度**。WayToAGI 要覆盖整个 AI 世界，本站只讲一颗芯片，因此每个知识点都要追到寄存器位、追到库源码行号、追到实测波形——讲不清出处的就明写"待核验"，不编。

## 事实从哪来

所有关键数值都有出处，写不出处的句子直接标"以某手册某节为准"。站内引证用到的一手资料：

| 资料 | 版本 / 提交 | 用在 |
|---|---|---|
| ST CMSIS 头文件 `stm32f407xx.h` + `core_cm4.h` | [cmsis_device_f4](https://github.com/STMicroelectronics/cmsis_device_f4) `v2.6.11` + [CMSIS_5](https://github.com/ARM-software/CMSIS_5) `5.9.0`（CI 逐字节校验 sha256） | 寄存器基址与位域核对（GPIO/RCC/DMA 等），S 篇与 C 篇引证；各章 `probe.sh` 的位号/地址对账第二来源 |
| STM32F4 HAL 驱动 | `stm32f4xx_hal_driver @ 1f6451c` | S2 RCC、S6 TIM、S7 USART、S8 DMA 的上游对照（rcc/tim/uart/dma 四个源文件均存档留证） |
| STM32F4 SPL（StdPeriph） | 官方未随 GitHub 分发，取自板卡资料盘 | S11 I2C、S15 库解剖 |
| FreeRTOS-Kernel | V11.1.0 + GCC/ARM_CM4F 移植层 | F 篇全部行号引证（ESP-IDF v5.5.2 内置的是 V10.5.1 SMP 改版，行号与结论不混读） |
| GD32F4xx 固件库 | V3.3.3 `@ 10d02f4` | G 篇 RCU/FMC 逐字段对照 |
| GD32VF103 固件库 + Bumblebee Core 手册 | `@ 7ab0521` | V 篇（RISC-V 线）CLIC/MTIME/工具链引证 |
| ESP-IDF | v5.5.2 | P 篇驱动框架与 soc_caps 结论 |
| RM0090 / STM32F407 datasheet | ST 官方 | 时钟树、复用表、电气参数 |
| 野火霸天虎开发指南与原理图 | 野火电子 | 板级事实：RGB 灯 PF6/7/8 共阳 |
| 立创·实战派 ESP32-S3 原理图与 wiki | 嘉立创 | 板级事实：N16R8、屏/双麦/喇叭/QMI8658、PSRAM 占 IO35/36/37 |

引证纪律与"禁止编造数值"的完整约束写在 [贡献指南](https://github.com/zhuguang-ZFG/mcu/blob/main/CONTRIBUTING.md)；手册修订号、协议规范版本、论文 DOI 与书目的完整清单在 [参考文献](bibliography.md)。

## 怎么参与

本站把四类工作都算贡献，都欢迎从 Issue 开始：

- **章节成稿**：按四件套（功能配置图解 / 引脚设置 / 库源码逐行 / 代码逐行分析）把骨架页写成稿；
- **动画**：把"看不见的机制"画成 SMIL SVG，每张必须能一句话说清它表达的结论；
- **实物实验**：在真实板卡上复现，配接线图与实测条件，禁止伪造照片；
- **勘误**：这一类最值钱。寄存器位、引脚号、版本号错一个，读者就要浪费一晚上。

每页右下角有"在 GitHub 上编辑此页"，改错了也不丢人。

## 致谢

- **[通往AGI之路](https://waytoagi.feishu.cn/)**：把"开源知识库可以这样组织"这件事做成了中文世界的样板，本站的地图、分流与名词前置都从这里来；
- **野火电子**：霸天虎的开发指南与原理图是板级事实的第一来源；
- **嘉立创 / 小智 AI**：实战派 ESP32-S3 与开源硬件音箱方案，让"能上手的 AIoT 板卡"变成几十块钱的事；
- **ST、GigaDevice、Espressif、FreeRTOS.org、RT-Thread、ARM（Cortex-M / Bumblebee）**：所有被逐行引用的上游源码作者——本站的教学建立在你们的工程之上，许可证与出处均已注明；
- **VitePress / Vue**：站点骨架；
- **每一位提 Issue 和勘误的读者**：这个项目最核心的资产是"错处被指出并改掉"的速度。

## 作者与维护

目前由 [@zhuguang-ZFG](https://github.com/zhuguang-ZFG) 独立撰写与维护，实验全部在作者手上的板卡完成。更新节奏见 [更新日志](/reference/changelog.md)。

## 许可证与免责

内容以 [Apache-2.0](https://github.com/zhuguang-ZFG/mcu/blob/main/LICENSE) 发布；引用的第三方源码遵守各自许可证。硬件操作有风险（供电、短路、烧毁引脚），本站的接线图与实验按作者实持板卡验证，你换板子请先自行核对原理图。站内标"待核验 / 待实测"的结论尚未闭环，请勿当作已验证数据引用。

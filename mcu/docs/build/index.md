---
title: B 篇导览
---

# 构建与运行全过程：你的代码经历了什么

> 🎯 多数人学嵌入式的盲区：点一下"编译下载"，中间两分钟发生的事一概不知。B 篇把这两分钟拉长成 8 章——看完你会知道：固件是怎么拼出来的、芯片上电后第一条指令是谁、断点为什么能让 CPU 停下来。

![B 篇路线总览：从四步构建到 SWD 调试的 8 站流水线](/anim/build-roadmap.svg)

## 章节路线

| 编号 | 章节 | 一句话精髓 |
|---|---|---|
| B0 | [工具链全景](00-toolchain.md) | 交叉编译四件套各管什么 |
| B1 | [四步构建](01-four-steps.md) | 预处理→编译→汇编→链接，逐步开盒 |
| B2 | [ELF 解剖](02-elf.md) | readelf/objdump 实拆一个固件 |
| B3 | [链接脚本](03-linker-script.md) | 内存布局的"建筑图纸"逐行讲 |
| B4 | [启动过程](04-startup.md)【成稿】 | 上电到 main 之间的每一条指令（动画） |
| B5 | [map 与体积](05-map-size.md) | 谁吃了你的 Flash/RAM |
| B6 | [烧录与调试](06-flash-debug.md) | SWD 两线协议与断点的硬件实现 |
| B7 | [构建系统](07-build-system.md) | Makefile→CMake/Ninja→IDF/scons 对照 |

## 学习建议

- B3+B4 是全站承上启下的枢纽：前面接 C 篇（段/符号），后面接裸机（启动文件）与 RTOS（栈/移植）；
- 每条命令都可以在 [code/stm32/00-blink](https://github.com/zhuguang-ZFG/mcu/tree/main/code/stm32/00-blink) 工程上跟着敲——B 篇的全部实验零额外装备。

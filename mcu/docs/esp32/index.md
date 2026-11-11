---
title: P 篇导览
---

# ESP32-S3 + ESP-IDF：小智板的里里外外

> 🎯 如果说 S 篇教会你"芯片的每个寄存器都是你家"，P 篇教你另一件事：**在一套全家桶框架里保持同样的洞察力**——IDF 给你 FreeRTOS、协议栈、驱动，但每个黑盒我们都会拆开看。

![P 篇路线总览：从环境搭建到音频全链路的 13 站纵深](/anim/esp32-roadmap.svg)

## 章节路线

| 编号 | 章节 | 一句话精髓 |
|---|---|---|
| P0 | [环境搭建](00-env.md)【成稿】 | IDF 四步曲，第一次对话 |
| P1 | [架构与启动](01-arch-boot.md) | 双核+Cache 世界，bootloader→app 接力 |
| P2 | [GPIO 与引脚矩阵](02-gpio-matrix.md)【成稿】 | Matrix 换岗实测，"任意引脚"的四个前提（动画 + 工程） |
| P3 | [IDF 工程解剖](03-idf-anatomy.md) | 组件化 CMake 与 Kconfig 流水线 |
| P4 | [中断与双核](04-irq-dualcore.md) | IRAM ISR 约束与核间通信 |
| P5 | [UART 驱动解析](05-uart-driver.md)【成稿】 | 事件驱动闭环与三层缓冲（动画 + 工程） |
| P6 | [SPI/I2C 驱动框架](06-spi-i2c-driver.md) | 拿板载屏幕与传感器当教材 |
| P7 | [定时器与 LEDC](07-timer-ledc.md)【成稿】 | GPTimer vs LEDC；S3 仅低速 8 通道（动画 + 工程） |
| P8 | [Wi-Fi 精髓](08-wifi.md) | 事件循环与连接状态机 |
| P9 | [蓝牙与 ESP-NOW](09-bt-espnow.md) | 协议栈架构与双板互传 |
| P10 | [Flash/分区/OTA](10-flash-nvs-ota.md) | 16MB 的版图与防变砖 |
| P11 | [低功耗](11-lowpower.md) | 睡眠矩阵与 ULP |
| P12 | [音频链路](12-audio-path.md) | ES8311+ES7210：小智的看家本领 |

## 与 S 篇的对照读法

- S 篇的每个外设章，在 P 篇找对应章：**S 篇讲"硬件真相"，P 篇讲"框架如何封装真相"**——两相对照，功力翻倍；
- RTOS 概念在 P 篇全部默认在线：F 篇的地基在这里天天用。

- [P13 看门狗与健康监督：不要喂反了](13-watchdog-health.md)：协议与故障恢复工程。

---
title: 综合项目
---

# 综合项目：两块板，同一套可验证的数据流

- [J1 F407 记录器](01-f407-logger.md)：ADC、DMA、EEPROM、FreeRTOS、IWDG。
- [J2 S3 记录器](02-s3-logger.md)：QMI8658、NVS、IDF、TWDT。

两者都完整实现采集、滤波、队列、协议、配置保存和健康恢复；共用主机工具。硬件实测状态与编译/模型验证分开。

# ESP32-S3：GPIO Matrix、UART、LEDC 内容与动画

## 目标与授权

父任务 [三路线内容深化与教学动画](../10-06-stm32-depth-animations/prd.md) 的第三批交付，依赖批次一、二已验收的跨路线对照结论。用户已审阅父任务方案并确认开始实施（2026-10-06），并确认手上有立创实战派 ESP32-S3 N16R8。

## 交付范围

| 项 | 内容 |
|---|---|
| 章节 | `docs/esp32/02-gpio-matrix.md`（P2）、`05-uart-driver.md`（P5）、`07-timer-ledc.md`（P7）三篇成稿 |
| 新动画 | `gpio-matrix-routing`、`idf-uart-events`、`ledc-timer-channel` |
| 配套工程 | `code/esp32/01-gpio-matrix`、`02-uart-events`、`03-ledc-fade` |
| 同步 | `docs/lab/e03-scope-pwm.md` 的 ESP32 部分（LEDC 实测口径） |

## 需求

- **PR1 版本纪律**：以本机 ESP-IDF **v5.5.x**（实际版本先读版本宏与 git 信息确认）为实施基准；芯片能力结论以 `components/soc/esp32s3/include/soc/soc_caps.h` 为准。不与 FreeRTOS 上游版本混用结论。
- **PR2 事实修复**：处理研究记录中归属本批次的缺陷 P-F1~P-F3（“任意引脚”须加芯片有效脚/输入输出能力/模组占用/板卡接线条件；IDF 5.5.x UART 源码已拆到 `components/esp_driver_uart/src/uart.c`，事件元数据不是串口字节负载；S3 不能套用经典 ESP32 的 16 通道与高速模式，LEDC 只有低速模式、8 通道、14 位定时器位宽、FIFO/队列语义按实际源码写）。
- **PR3 引脚纪律**：所有示例引脚必须落到立创实战派对应板版本的原理图/官方资料；取不到一手资料时不写默认值，改为显式配置点并说明依据缺口。
- **PR4 因果链**：每章走通“配置对象 → 驱动/HAL/芯片能力 → ISR/缓冲/用户任务或输出引脚”。
- **PR5 可复现**：三个工程各自可 `idf.py set-target esp32s3` + `idf.py build` 通过，README 写明 IDF 版本、构建命令、观察方式与排查；`idf.py size` 结果留证。
- **PR6 动画**：三张图分别表达“外设信号经 Matrix/IO_MUX 到焊盘的路由与约束”“字节 FIFO → ring buffer → 用户缓冲，事件描述另走 queue → task”“timer 定频率与分辨率、channel 定 GPIO 与占空比、fade 更新比较值”。

## 验收标准

- [ ] PA1 / PR1：三章的 IDF API 与路径对应本机 v5.5.x 实际源码位置。
- [ ] PA2 / PR2：P-F1~P-F3 逐条处置。
- [ ] PA3 / PR3：无未核实引脚；每个示例引脚有一手来源。
- [ ] PA4 / PR5：三个工程 `idf.py build` 通过，README 完整。
- [ ] PA5 / PR6：三张动画被引用、无孤儿，图形核验通过。
- [ ] PA6：`npm run docs:build` 零错误。

## 范围边界

不含 wifi/蓝牙/音频章节成稿、不含 NVS/OTA 章节、不改播放器与导航结构。IDF 源码只作为本机依赖引用，不入库。

## 依赖

- 批次一（时钟树/PWM/串口）与批次二（通知/事件/定时器/堆）的跨路线对照结论。
- 本机 ESP-IDF v5.5.x 环境。
- 立创实战派 ESP32-S3 实机与其原理图资料。
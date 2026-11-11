# 双板记录器验证记录（C-A1–C-A6）

记录于 2026-10-08 收口（由 TeleAgent 接手并行会话成果并验证）。

## 验证环境与口径

- 本机：Windows + `arm-none-eabi-gcc 15.2.1` + mingw64 `gcc` + Git Bash（`sh`/`mkdir -p`）；**ESP-IDF 未完整安装**（`C:\Espressif` 仅 tools/dist），S3 依赖既有构建产物与 CI 构建。
- CI：GitHub Actions（Linux），`firmware:check`/`docs:build` 等以 CI 结果为准（本机 mingw 下 `mkdir -p` 类 Unix 命令不适用，属环境差异非代码缺陷）。
- 口径：**编译/模型/门禁通过 ≠ 上板通过**。所有外设观测标注 `pending`，与 `hardware_status` 一致。

## C-A1 两平台完整驱动与任务实现

| 项 | 结果 | 证据 |
|---|---|---|
| F407（stm32/07-sensor-logger）真实 ADC1(PA0)/TIM2 TRGO/DMA2 Stream0、AT24C02 双槽位带 I2C、IWDG、FreeRTOS 任务 | 通过（可复现构建） | `mingw32-make -B MODE=0 FAULTS=0/1` 均 exit 0；text 18656/18756 B |
| ESP32-S3（esp32/08-sensor-logger）真实 QMI8658（I2C GPIO1/2）、NVS 独立 namespace、独立 watchdog、IDF 任务 | 产物验证 | `build/recovery-faults/sensor-logger.bin`（256 288 B，target=esp32s3）；本机 IDF 缺失，CI 构建覆盖 |
| 共享 logger 核心（纯 C） | 通过 | `sh code/common/logger/probe.sh`：framing/filter/backpressure/EEPROM 写中断恢复全部 passed |
| 无占位采样/模拟存储 | 通过 | port.h/logger_port.c 走真实外设寄存器路径，宿主替身仅用于测试 |

## C-A2 同一 CLI 双板语义一致

| 项 | 结果 | 证据 |
|---|---|---|
| `scripts/device-console.py` INFO/STATUS/START/STOP/SET_CONFIG/SAVE_CONFIG/record/save/configure 子命令 | 通过 | 模块导入即验证；`parse_sample`/`parse_tlvs` 独立解码 64B 帧与 TLV |
| 主机侧解码测试 | 通过 | `tests/logger-cli.test.mjs`：64B 帧、TLV、截断拒绝、非法配置本地拒绝（不碰串口）；npm test 60/60 绿 |
| 传感器类型/单位/有效字段 | 通过（文档口径） | INFO TLV 返回量程/换算；ADC sensor_type=1、IMU=2；不跨传感器比较原始值 |
| 双板真实串口交互 | pending | 需两板接线后按同一命令矩阵实测 |

## C-A3 正常流与背压

| 项 | 结果 | 证据 |
|---|---|---|
| 16 槽队列满丢新样本并计数 | 通过（模型） | probe.sh 背压断言 |
| 消费慢只增 drop，不阻塞采集/监督 | 通过（模型） | 采样优先级高于通信；host 断言覆盖 |
| 稳定序号/时间戳/原始/滤波、代次边界 | 通过（模型/单测） | logger-contract.md；generation 有界模序号 |
| 上板连续记录 | pending | 待 F407/S3 实测 |

## C-A4 配置写入故障恢复

| 项 | 结果 | 证据 |
|---|---|---|
| AT24C02 双 128B 槽：先失效→8B 页写→回读校验→commit marker | 通过（模型注入） | probe.sh 每步写中断恢复断言全过 |
| 写中断后重启只恢复旧或新完整配置 | 通过（模型注入） | 同上；CRC/schema 错误走安全默认 |
| 两槽无效显式默认并上报 | 通过（代码路径） | store.c；文档写明 |
| 真实 EEPROM/NVS 断电试验 | pending | 需上板断电注入 |

## C-A5 故障注入矩阵

| 故障 | 模型 | 硬件 |
|---|---|---|
| sensor disconnect（valid_mask 置位、滤波不复用旧值/不填零） | 通过 | pending |
| CRC 损坏帧 | 通过（logger-cli 拒绝截断/坏帧） | pending |
| 消费暂停（队列满丢新） | 通过（probe.sh） | pending |
| 任务 freeze（监督不喂狗→watchdog 复位并报告原因） | 实现就位（IWDG/TWDT） | pending（需实测复位原因） |
| 配置损坏/中断写入 | 通过（C-A4） | pending（断电） |

## C-A6 干净 checkout 端到端

| 项 | 结果 |
|---|---|
| docs/projects/index.md、01-f407-logger.md、02-s3-logger.md（接线、数据样本格式、配置占用、排查） | 成稿；浏览器端到端覆盖两页（源码暴露 + 待上板状态） |
| 导航/计划/统计登记 | 全站 107 页可达（nav:check）；80 章/8 实验/55 动画/37 工程（readme:check） |
| 质量门禁 | quality 全绿 + test:browser 5/5（搜索修复后复验） |
| 真实数据样本回填 | 待上板后用同一 device-console 产出 |

## 收口时发现并修复的问题

- **搜索回归（真实 bug）**：`scripts/search-tokenize.mjs` 的 `tokenizeForSearch` 引用模块级常量，VitePress 反序列化函数到浏览器后作用域丢失，每次搜索抛 `ReferenceError: SPACE_OR_PUNCTUATION is not defined`、结果为空。修复：函数体自包含（常量内联）；复检 'I2C' 16 条命中、'优先级反转' 首条命中实验 E04。
- 本机 `firmware:check` 因 Windows 缺 `sh`/`mkdir -p` 无法全量（CI 覆盖）；`esp32-08` 需 IDF 环境（本机未装，产物+CI 覆盖）。

> AI生成
